import { WEBUI_API_BASE_URL } from '$lib/constants';

export const queryPyScriptsByName = async (token: string, name: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/scripts/?name_like=${name}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`
    },
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .then((json) => {
      return json;
    })
    .catch((err) => {
      error = err.detail;
      console.log(err);
      return null;
    });

  return res;
}

export const createNewPyScripts = async (token: string, script: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/scripts/`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      ...script
    })
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail;
      console.log(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const listPyScripts = async (token: string = '') => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/scripts/`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`
    }
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .then((json) => {
      return json;
    })
    .catch((err) => {
      error = err.detail;
      console.log(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const getPyScriptById = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/scripts/${id}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`
    }
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .then((json) => {
      return json;
    })
    .catch((err) => {
      error = err.detail;

      console.log(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const updatePyScriptById = async (token: string, id: string, script: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/scripts/${id}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      ...script
    })
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .then((json) => {
      return json;
    })
    .catch((err) => {
      error = err.detail;

      console.log(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const deletePyScriptById = async (token: string, id: string) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/scripts/${id}`, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      authorization: `Bearer ${token}`
    }
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .then((json) => {
      return json;
    })
    .catch((err) => {
      error = err.detail;

      console.log(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};