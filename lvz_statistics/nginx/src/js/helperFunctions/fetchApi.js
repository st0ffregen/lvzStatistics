async function fetchApi(route, parameter = '', parameterValue = '') {
    let response;

    if (parameter === '' && parameterValue === '') {
        response = await fetch('api/' + route);
    } else {
        response = await fetch('api/' + route + '?' + parameter + '=' + parameterValue);
    }

    return await response.json();
}
