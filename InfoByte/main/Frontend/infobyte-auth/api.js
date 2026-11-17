async function api(path, method = "GET", data) {
  const options = {method, credentials: "same-origin"};
  if (data !== undefined) {
    options.headers = {"Content-Type": "application/json"};
    options.body = JSON.stringify(data);
  }
  const response = await fetch("/api" + path, options);
  if (response.status === 204) return;
  const result = await response.json();
  if (!response.ok) {
    const fields = (result.errors || []).map(e => e.field + " — " + e.message);
    const error = new Error([result.detail, ...fields].join(" "));
    error.status = response.status;
    throw error;
  }
  return result;
}
