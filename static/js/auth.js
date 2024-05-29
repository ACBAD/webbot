let token_hash = '';

function getCookie(name) {
    let cookieArr = document.cookie.split(";");
    for (let i = 0; i < cookieArr.length; i++) {
        let cookiePair = cookieArr[i].split("=");
        if (name === cookiePair[0].trim()) {return decodeURIComponent(cookiePair[1]);}
    }
    return null;
}

function sha256(message) {return CryptoJS.SHA256(message).toString(CryptoJS.enc.Hex);}
function calculat_hask_token() {
    document.getElementById('upload_msg').innerText = "正在计算鉴权令牌";
    let cookieName = "authToken";
    let cookieValue = getCookie(cookieName);
    document.getElementById("upload_msg").innerText = cookieValue;
    if (cookieValue) {
        token_hash = sha256(cookieValue);
        document.getElementById('upload_msg').innerText = token_hash;
        document.getElementById('upload_msg').innerText = "鉴权令牌计算完成";
    } else {
        token_hash = 'Undefined'
        document.getElementById('upload_msg').innerText = "你没设置cookie";
        //alert('你没设置Token');
    }
}
window.onload = function () {calculat_hask_token();};
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

document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // 阻止表单的默认提交行为
    const fileInput = document.getElementById('image');
    const file = fileInput.files[0];
    if (!file) {
        alert('请选择文件');
        return;
    }
    // 计算文件的MD5值
    const md5 = await calculateMD5(file);
    // 获取文件扩展名
    const ext = getFileExtension(file.name);
    // 创建一个隐藏的表单并附加数据
    const form = document.createElement('form');
    if(token_hash === ''){
        alert('鉴权令牌未计算完成，请等待！');
        return;
    }
    else if(token_hash === 'Undefined'){
        alert('未设置cookie，无法计算鉴权令牌');
        return;
    }
    form.method = 'POST';
    form.action = '/bot/upload_imgs/' + token_hash;
    form.enctype = 'multipart/form-data';
    // 创建并附加文件输入
    const fileInputHidden = document.createElement('input');
    fileInputHidden.type = 'file';
    fileInputHidden.name = 'image';
    fileInputHidden.files = fileInput.files;
    form.appendChild(fileInputHidden);
    // 创建并附加 MD5 输入
    const md5Input = document.createElement('input');
    md5Input.type = 'hidden';
    md5Input.name = 'md5';
    md5Input.value = md5;
    form.appendChild(md5Input);
    // 创建并附加扩展名输入
    const extInput = document.createElement('input');
    extInput.type = 'hidden';
    extInput.name = 'ext';
    extInput.value = ext;
    form.appendChild(extInput);
    document.body.appendChild(form);
    document.getElementById('upload_msg').innerText = '请求构造完成，开始上传'
    form.submit();
});

async function calculateMD5(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (event) => {
            const arrayBuffer = event.target.result;
            const wordArray = CryptoJS.lib.WordArray.create(arrayBuffer);
            const md5 = CryptoJS.MD5(wordArray).toString();
            resolve(md5);
        };
        reader.onerror = (error) => reject(error);
        reader.readAsArrayBuffer(file);
    });
}

function getFileExtension(filename) {return filename.split('.').pop();}