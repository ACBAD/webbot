$(document).ready(function() {
    $('#ajax-form').on('submit', function(event) {
        event.preventDefault(); // 防止表单默认提交
        var name = $('#name').val();
        $.ajax({
            type: 'POST',
            url: '/ajax_test',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({name: name}),
            success: function(response) {
                $('#response').html(response.message);
            },
            error: function(error) {
                $('#response').html('An error occurred');
            }
        });
    });
});
