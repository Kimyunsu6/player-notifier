import { verifyKey, InteractionType, InteractionResponseType } from "discord-interactions";

export default {
  async fetch(request, env) {
    // 브라우저로 접속하면 (POST가 아니면) 동작 확인 문구만 보여주기
    if (request.method !== "POST") {
      return new Response("bot-worker is running");
    }

    // 1. 디스코드가 보낸 게 맞는지 서명 검사
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

    // 2. 디스코드의 연결 확인 (PING) -> PONG
    if (interaction.type === InteractionType.PING) {
      return Response.json({ type: InteractionResponseType.PONG });
    }

    // 3. 슬래시 명령어
    if (interaction.type === InteractionType.APPLICATION_COMMAND) {
      const name = interaction.data.name;

      if (name === "핑") {
        return reply("퐁!");
      }

      return reply("모르는 명령어예요.");
    }

    return new Response("unknown type", { status: 400 });
  }
};

// 채널에 텍스트로 대답하기
function reply(text) {
  return Response.json({
    type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
    data: { content: text }
  });
}