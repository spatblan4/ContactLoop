import { supabase } from './supabase.js';

function authClient(client = supabase) {
  if (!client?.auth) throw new Error('Supabase Auth is not configured.');
  return client.auth;
}

export async function getAuthSession(client = supabase) {
  const { data, error } = await authClient(client).getSession();
  if (error) throw error;
  return data.session;
}

export function signInWithPassword(email, password, client = supabase) {
  return authClient(client).signInWithPassword({ email, password });
}

export function signUpWithPassword(email, password, client = supabase) {
  return authClient(client).signUp({ email, password });
}

export async function signOut(client = supabase) {
  const { error } = await authClient(client).signOut();
  if (error) throw error;
}

export function subscribeToAuthChanges(callback, client = supabase) {
  return authClient(client).onAuthStateChange(callback);
}
