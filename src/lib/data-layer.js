import * as facade from './supabase.js';

export function requireFacadeAction(name) {
  const action = facade[name];
  if (typeof action !== 'function') {
    throw new Error('This action is not available in the current data layer configuration.');
  }
  return action;
}
