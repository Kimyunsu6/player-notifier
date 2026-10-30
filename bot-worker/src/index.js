import { verifyKey, InteractionType, InteractionResponseType } from "discord-interactions";

const MAX_PLAYERS = 10;      // 1인당 최대 선수 수
let playerDbCache = null;    // 선수 사전 (한 번 읽으면 기억)


// ===== 메인: 디스코드 요청 처리 =====
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("bot-worker is running");
    }

    // 1. 서명 검사
    const signature = request.headers.get("X-Signature-Ed25519");
    const timestamp = request.headers.get("X-Signature-Timestamp");
    const body = await request.text();

    if (!signature || !timestamp) {
      return new Response("missing signature", { status: 401 });
    }
    const isValid = await verifyKey(body, signature, timestamp, env.DISCORD_PUBLIC_KEY);
    if (!isValid) {
      return new Response("bad signature", { status: 401 });
    }

    const interaction = JSON.parse(body);

    // 2. 연결 확인
    if (interaction.type === InteractionType.PING) {
      return Response.json({ type: InteractionResponseType.PONG });
    }

    // 3. 자동완성 (입력하는 중)
    if (interaction.type === 4) {
      return await handleAutocomplete(interaction, env);
    }

    // 4. 명령어 실행 (Enter 눌렀을 때)
    if (interaction.type === InteractionType.APPLICATION_COMMAND) {
      return await handleCommand(interaction, env);
    }

    return new Response("unknown type", { status: 400 });
  }
};


// ===== 자동완성 =====
async function handleAutocomplete(interaction, env) {
  const commandName = interaction.data.name;
  const typed = simplify(getOption(interaction, "선수") || "");
  const choices = [];

  if (commandName === "선수추가") {
    if (typed.length >= 2) {
      const db = await getPlayerDb(env);
      for (const p of db) {
        if (simplify(p.name).includes(typed)) {
          choices.push({ name: p.name + " (" + p.team + ")", value: p.id });
          if (choices.length >= 25) {
            break;      // 디스코드는 최대 25개까지
          }
        }
      }
    }
  }

  if (commandName === "선수삭제") {
    const user = await getUser(env, getUserId(interaction));
    for (const p of user.players) {
      if (simplify(p.name).includes(typed)) {
        choices.push({ name: p.name, value: p.id });
      }
    }
  }

  // type 8 = 자동완성 결과
  return Response.json({ type: 8, data: { choices: choices } });
}


// ===== 명령어 =====
async function handleCommand(interaction, env) {
  const commandName = interaction.data.name;
  const userId = getUserId(interaction);

  if (commandName === "핑") {
    return reply("퐁!");
  }

  if (commandName === "선수추가") {
    const playerId = getOption(interaction, "선수");
    const db = await getPlayerDb(env);

    // 사전에서 ID로 찾기
    let found = null;
    for (const p of db) {
      if (p.id === playerId) {
        found = p;
      }
    }
    if (found === null) {
      return reply("목록에서 선수를 골라주세요. (이름을 2글자 이상 입력하면 후보가 나와요)");
    }

    const user = await getUser(env, userId);

    for (const p of user.players) {
      if (p.id === found.id) {
        return reply(found.name + " 선수는 이미 등록되어 있어요.");
      }
    }
    if (user.players.length >= MAX_PLAYERS) {
      return reply("최대 " + MAX_PLAYERS + "명까지 등록할 수 있어요. /선수삭제 후 다시 추가해 주세요.");
    }

    user.players.push({ id: found.id, name: found.name });
    user.guild_id = interaction.guild_id;
    await saveUser(env, userId, user);

    return reply(found.name + " (" + found.team + ") 추가 완료! 현재 " + user.players.length + "명");
  }

  if (commandName === "선수삭제") {
    const playerId = getOption(interaction, "선수");
    const user = await getUser(env, userId);

    const newList = [];
    let removedName = "";
    for (const p of user.players) {
      if (p.id === playerId) {
        removedName = p.name;
      } else {
        newList.push(p);
      }
    }
    if (removedName === "") {
      return reply("등록되지 않은 선수예요. 목록에서 골라주세요.");
    }

    user.players = newList;
    await saveUser(env, userId, user);
    return reply(removedName + " 삭제 완료. 현재 " + user.players.length + "명");
  }

  if (commandName === "내선수") {
    const user = await getUser(env, userId);
    if (user.players.length === 0) {
      return reply("등록된 선수가 없어요. /선수추가 로 추가해 보세요.");
    }

    const db = await getPlayerDb(env);
    let text = "**내 선수 (" + user.players.length + "/" + MAX_PLAYERS + ")**\n";
    for (const p of user.players) {
      let team = "4대 리그 밖";
      for (const d of db) {
        if (d.id === p.id) {
          team = d.team;
        }
      }
      text = text + "- " + p.name + " (" + team + ")\n";
    }

    const o = user.options;
    text = text + "\n**알림 옵션**\n";
    text = text + "선발/벤치: " + onOff(o.lineup) + "  ·  골/어시: " + onOff(o.goals) + "  ·  결과: " + onOff(o.result);
    return reply(text);
  }

  return reply("모르는 명령어예요.");
}


// ===== 도우미 함수 =====

// 나만 보이는 메시지로 대답 (flags 64)
function reply(text) {
  return Response.json({
    type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
    data: { content: text, flags: 64 }
  });
}

// 명령어 옵션 값 꺼내기
function getOption(interaction, name) {
  const options = interaction.data.options || [];
  for (const o of options) {
    if (o.name === name) {
      return o.value;
    }
  }
  return null;
}

// 명령어 친 사람 ID (서버면 member, DM이면 user)
function getUserId(interaction) {
  if (interaction.member) {
    return interaction.member.user.id;
  }
  return interaction.user.id;
}

// 검색용: 소문자 + 악센트 제거 (Mbappé -> mbappe)
function simplify(text) {
  return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function onOff(value) {
  if (value) {
    return "켜짐";
  }
  return "꺼짐";
}

// KV에서 선수 사전 읽기 (처음 한 번만)
async function getPlayerDb(env) {
  if (playerDbCache === null) {
    playerDbCache = await env.SETTINGS.get("player_db", "json");
    if (playerDbCache === null) {
      playerDbCache = [];
    }
  }
  return playerDbCache;
}

// KV에서 사용자 설정 읽기 (없으면 기본값)
async function getUser(env, userId) {
  const data = await env.SETTINGS.get("user:" + userId, "json");
  if (data === null) {
    return { players: [], options: { lineup: true, goals: true, result: true }, guild_id: null };
  }
  return data;
}

// KV에 사용자 설정 저장
async function saveUser(env, userId, data) {
  await env.SETTINGS.put("user:" + userId, JSON.stringify(data));
}