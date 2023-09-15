// Обработчик события клика по кнопке лайка
$('.like-button').click(function () {
    let taskId = $(this).data('task-id');
    let likeButton = $(this);

    $.post('/like/' + taskId, function (data) {
        likeButton.siblings('.like-count').text(data.likes);

        if (data.liked) {
            likeButton.find('i').removeClass('far').addClass('fas');
        } else {
            likeButton.find('i').removeClass('fas').addClass('far');
        }

        // Обновляем состояние liked для следующего клика
        data.liked = !data.liked;

        // Выводим имя пользователя, если лайк установлен
        if (data.user !== null) {
            console.log('Лайк установлен пользователем:', data.user);
        } else {
            console.log('Лайк снят');
        }

    }, 'json');
});
