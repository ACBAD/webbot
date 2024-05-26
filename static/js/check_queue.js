$(document).ready(function() {
    $('#form_jmid').on('submit', function(event) {
        event.preventDefault(); // 防止表单默认提交
        $.ajax({
            type: 'POST',
            url: '/bot/req_queue',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({ type: 'jm' }),
            success: function(response) {
                $('#jm_ajax_response').html(response.message);
                setTimeout(function() {
                    $('#form_jmid').off('submit').submit(); // 取消阻止默认行为后提交表单
                }, 1000); // 延迟1秒
            },
            error: function(error) {
                $('#jm_ajax_response').html('An error occurred');
            }
        });
    });

    $('#form_pid').on('submit', function(event){
        event.preventDefault(); // 防止表单默认提交
        $.ajax({
            type: 'POST',
            url: '/bot/req_queue',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({ type: 'pixiv' }),
            success: function(response) {
                $('#pixiv_ajax_response').html(response.message);
                setTimeout(function() {
                    $('#form_pid').off('submit').submit(); // 取消阻止默认行为后提交表单
                }, 1000); // 延迟1秒
            },
            error: function(error) {
                $('#pixiv_ajax_response').html('An error occurred');
            }
        });
    });
});
