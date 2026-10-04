export async function api<T>(path:string, method='GET', body?:unknown):Promise<T> {
  const response = await fetch('/api'+path, {method, headers:body instanceof FormData ? undefined : {'Content-Type':'application/json'},
    body:body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body)})
  const data = await response.json()
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Eingaben sind unvollständig oder ungültig.')
  return data as T
}
