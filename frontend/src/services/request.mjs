export function buildApiHeaders(authenticationHeaders = {}, hasJsonBody = false) {
  return hasJsonBody
    ? { 'Content-Type': 'application/json', ...authenticationHeaders }
    : { ...authenticationHeaders };
}
