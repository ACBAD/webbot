const redirect_button = document.getElementById('redirect_to_hitomi')

function set_button(action){
    $('#redirect_to_hitomi').prop('disabled', action);
    $('#jm_submit_button').prop('disabled', action);
}

redirect_button.addEventListener('click', function () {
    set_button(true);
    if(typeof(EventSource)!=='undefined'){
        const jm_str = $('#jmid').value;
        let source = new EventSource('/bot/redirect_to_hitomi?jm_str=' + jm_str);
        source.onopen = function (ev){
            $('#jm_ajax_response').innerText = 'SSE链接已建立';
        }
        source.onmessage = function (ev){
            /** @type {{echo: string, status: string, type: string}} */
            let server_response = JSON.parse(ev.data);
            if(server_response.type === 'json'){
                $('#jm_ajax_response').innerText = server_response.echo;
                if(server_response.status === 'error'){
                    set_button(false);
                    source.close();
                }
            }
            else if(server_response.type === 'redirect'){
                window.location.href = server_response.echo;
            }
        }
        source.onerror = function (ev){
            $('#jm_ajax_response').innerText = 'SSE链接发生错误';
            console.error('SSE ERROR: ', ev);
            source.close();
        }
    }
    else {
        $('#jm_ajax_response').innerText = '不是哥们，都什么年代了，你的浏览器还不支持SSE？';
        set_button(false);
    }
    // $.ajax({
    //     type: 'POST',
    //     url: '/bot/redirect_to_hitomi',
    //     contentType: 'application/json;charset=UTF-8',
    //     data: JSON.stringify({type: 'search', query_str: $('#jmid').value}),
    //     success: function (response) {
    //
    //         set_button(false);
    //     },
    //     error: function (){
    //         $('#jm_ajax_response').innerText = '后端请求出错';
    //         set_button(false);
    //     }
    // })
})