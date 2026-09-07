const TOKEN_KEY = 'contactloop.auth.token';

let memoryToken = null;

function storage() {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null;
  }
}

export function getStoredToken() {
  const store = storage();
  if (store) {
    try {
      return store.getItem(TOKEN_KEY) ?? null;
    } catch {
      // fall through to the in-memory token
    }
  }
  return memoryToken;
}

export function setStoredToken(token) {
  const store = storage();
  if (store) {
    try {
      if (token) store.setItem(TOKEN_KEY, token);
      else store.removeItem(TOKEN_KEY);
      return;
    } catch {
      // fall through to the in-memory token
    }
  }
  memoryToken = token || null;
}

export function clearStoredToken() {
  setStoredToken(null);
}
