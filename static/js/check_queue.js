$(document).ready(function() {
    $('#form_jmid').on('submit', function(event) {
        event.preventDefault(); // 防止表单默认提交
        $.ajax({
            type: 'POST',
            url: '/req_queue',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({ type: 'jm' }),
            success: function(response) {
                $('#jm_ajax_response').html(response.message);
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
            url: '/req_queue',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({ type: 'pixiv' }),
            success: function(response) {
                $('#pixiv_ajax_response').html(response.message);
            },
            error: function(error) {
                $('#pixiv_ajax_response').html('An error occurred');
            }
        });
    });
});
