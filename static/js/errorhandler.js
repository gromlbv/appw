function handleResponse(event) {
    const xhr = event.detail.xhr;
    const target = event.detail.target;
    
    target.classList.remove('error', 'warning', 'info', 'success', 'show-response');
    target.innerHTML = 'Загрузка...';

    try {
        const contentType = xhr.getResponseHeader('Content-Type');
        let response;
        
        if (contentType && contentType.includes('application/json')) {
            response = JSON.parse(xhr.responseText);
        } else {
            throw new Error('Получил HTML вместо JSON');
        }

        let responseType, responseMessage;
        
        if (response.type && typeof response.type === 'object') {
            responseType = response.type.type || 'error';
            responseMessage = response.type.message || 'Неизвестная ошибка';
        } else {
            responseType = response.type || 'error';
            responseMessage = response.message || 'Неизвестная ошибка';
        }

        let messageHTML = `<span class="response-message">${responseMessage}</span>`;
        
        if (response.icon) {
            messageHTML = `<i class="response-icon ${response.icon}"></i> ` + messageHTML;
        }

        target.innerHTML = messageHTML;
        target.classList.add(responseType, 'show-response');

        if (responseType === 'info' || responseType === 'success') {
            setTimeout(() => {
                target.classList.remove('show-response');
            }, 5000);
        }

        if (response.redirect_to) {
            window.location.href = response.redirect_to;
        }

    } catch (e) {
        console.error('Возникла ошибка... ', e);
        
        target.innerHTML = `
            <span class="response-message">
                Ошибка сервера. Пожалуйста, попробуйте позже или 
                <a href="/support">Обратитесь в поддержку</a>
            </span>
        `;
        target.classList.add('error', 'show-response');
    }
}