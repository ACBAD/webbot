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
    let token_hash;
    document.getElementById('upload_msg').innerText = "正在计算鉴权令牌";
    let cookieName = "authToken";
    let cookieValue = getCookie(cookieName);
    document.getElementById("upload_msg").innerText = cookieValue;
    if (cookieValue) {
        token_hash = sha256(cookieValue);
        document.getElementById('upload_msg').innerText = "鉴权令牌计算完成";
    } else {token_hash = 'Undefined';}
    return token_hash;
}
window.onload = function () {calculat_hask_token();};


document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    $('#upload_submit_button').prop('disabled', true);
    const fileInput = document.getElementById('image');
    const file = fileInput.files[0];
    if (!file) {
        alert('请选择文件');
        return;
    }
    const req_url = '/bot/upload_imgs/' + calculat_hask_token();
    document.getElementById('upload_msg').innerText = '请求构造完成，开始上传';
    const formData = new FormData();
    formData.append('ext', getFileExtension(file.name));
    formData.append('md5', await calculateMD5(file));
    formData.append('image', file);
    $.ajax({
        url: req_url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function (response){
            if(response.startsWith('nmsl')){
                let htmlRes = response.slice(4);
                document.write(htmlRes);
                return;
            }
            if(typeof(EventSource)!=='undefined'){
                let source = new EventSource(req_url + '/' + response);
                source.onopen = function (enent){
                    document.getElementById('upload_msg').innerText = 'SSE链接已建立';
                }
                source.onmessage = function (event){
                    /** @type {{echo: string, status: string, type: string}} */
                    let jsonObj = JSON.parse(event.data);
                    if(jsonObj.type === 'json'){
                        document.getElementById('upload_msg').innerText = jsonObj.echo;
                        if(jsonObj.status === 'error'){
                            $('#upload_submit_button').prop('disabled', false);
                            source.close();
                        }
                    }
                    else if(jsonObj.type === 'html'){
                        let html = jsonObj.echo;
                        console.log(html)
                        source.close();
                        document.open();
                        document.write(html);
                        document.close();
                    }
                    else document.getElementById('upload_msg').innerText = '服务器返回了无法解析的信息...';
                };
                source.onerror = function (evnet){
                    document.getElementById('upload_msg').innerText = 'SSE链接发生错误';
                    console.error('EventSource failed:' , event);
                    source.close();
                };
            }
            else {
                document.getElementById('upload_msg').innerText = '你还在用什么上古浏览器！连SSE都不支持？';
            }
        },
        error: function (){
            document.getElementById('upload_msg').innerText = '与服务器通信时失败...';
            document.getElementById('upload_submit_button').prop('disabled', false);
        }
    })
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