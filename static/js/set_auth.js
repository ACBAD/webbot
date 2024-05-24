function setCookie(name, value) {
    const expires = "Fri, 31 Dec 9999 23:59:59 GMT";
    document.cookie = name + "=" + (value || "") + "; expires=" + expires + "; path=/";
}
function handleFormSubmit(event) {
    event.preventDefault();
    let inputValue = document.getElementById('auth_token').value;
    setCookie('authToken', inputValue);
    document.getElementById('auth_msg').innerHTML = '你的AuthToken已保存';
}