import { supabase, hasBackendConfig, hasSupabaseConfig } from './supabase.js';
import * as backendAuth from './api/auth.js';

function useBackendAuth() {
  return !hasSupabaseConfig && hasBackendConfig();
}

function sessionFromUser(user) {
  if (!user) return null;
  return { user: { id: user.id, email: user.email, name: user.name ?? null } };
}

function authClient(client = supabase) {
  if (!client?.auth) throw new Error('Supabase Auth is not configured.');
  return client.auth;
}

export async function getAuthSession(client = supabase) {
  if (client === supabase && useBackendAuth()) {
    return sessionFromUser(await backendAuth.fetchMe());
  }
  const { data, error } = await authClient(client).getSession();
  if (error) throw error;
  return data.session;
}

export async function signInWithPassword(email, password, client = supabase) {
  if (client === supabase && useBackendAuth()) {
    try {
      const user = await backendAuth.login({ email, password });
      return { data: { session: sessionFromUser(user) }, error: null };
    } catch (error) {
      return { data: { session: null }, error };
    }
  }
  return authClient(client).signInWithPassword({ email, password });
}

export async function signUpWithPassword(email, password, client = supabase) {
  if (client === supabase && useBackendAuth()) {
    try {
      const user = await backendAuth.register({ email, password, name: null });
      return { data: { session: sessionFromUser(user) }, error: null };
    } catch (error) {
      return { data: { session: null }, error };
    }
  }
  return authClient(client).signUp({ email, password });
}

export async function signOut(client = supabase) {
  if (client === supabase && useBackendAuth()) {
    await backendAuth.logout();
    return;
  }
  const { error } = await authClient(client).signOut();
  if (error) throw error;
}

export function subscribeToAuthChanges(callback, client = supabase) {
  if (client === supabase && useBackendAuth()) {
    return { unsubscribe() {} };
  }
  return authClient(client).onAuthStateChange(callback);
}
