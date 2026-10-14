import { createClient } from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/api/_generated/client/client.gen';
interface Resource { id: number; name: string; }
const client = createClient();
client.sse.get<{ 200: Resource }>({ url: '/events', onSseEvent(event) {
  const id: number = event.data.id;
  void id;
}});
