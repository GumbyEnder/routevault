import { getStore, currentUser, json, profilePayload } from '../../lib/legacy-server.mjs';
export async function GET({ request }) {
  const user = await currentUser(request);
  if (!user) return json({ user: null, accounts: true });
  const store = await getStore();
  const profile = await store.getProfile(user.id);
  return json(profilePayload(user, profile, { accounts: true }));
}
