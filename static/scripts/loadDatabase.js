const fileInput = document.querySelector('#inputFile');
const dateInput = document.querySelector('#inputDate');
const fileLabel = document.querySelector('#labelFile');
const dateLabel = document.querySelector('#labelDate');
const resultLabel = document.querySelector('#labelResult');
const readButton = document.querySelector('#readButton');
const sendButton = document.querySelector('#sendButton');

let dataText = [];

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};


function sendString (string) {
    url = `http://127.0.0.1:8000/import/database-load-record/`;
    return fetch(url, {
        method: 'POST',
        body: JSON.stringify(string), // данные могут быть 'строкой' или {объектом}!
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFTOKEN': getCookie('csrftoken'),
        }
    })
        .then((response) => {
            if(!response.ok){ throw new Error() };
            return response.json();
        })
        .then((json) => {
            return json;
        })
        .catch((error) => { alert('Проблема с выполнением запроса !') });
};


function readFile(file){
    // создаем экземпляр объекта "FileReader"
    const reader = new FileReader()
    // читаем файл как текст, вторым аргументом является кодировка
    // по умолчанию - utf-8, но она не понимает кириллицу
    reader.readAsText(file, 'windows-1251')
    dataText = [];
    // дожидаемся завершения чтения файла и помещаем результат в документ
    reader.onload = () => {
        // разбиваем текст на строки и обрабабатывае построчно
        let strings = reader.result.replace('\r','').split('\n');
        let count = 0;
        let acceptCount = 0;
        let header = [];
        for (stringInd in strings){
            // первая строка заголовок
            if(count==0){
                header = strings[stringInd].split('\t');
            }else{
                let dataString = {};
                // разбиваем стркоу на значения по Tab
                const values = strings[stringInd].split('\t');
                // создаем словарь с ключами из header
                for(valueInd in values){ dataString[header[valueInd]] = values[valueInd] };
                // если в нужном диапазоне дат добавляем объект в стрктуру данных
                if(dateInput.value){
                    const selectDate = new Date(dateInput.value);
                    if (dataString['ACCEPTDATE']){
                        const fileDate = new Date(dataString['ACCEPTDATE'].split(' ')[0]);
                        if(fileDate >= selectDate){
                            dataText.push(dataString);
                            acceptCount++;
                        };
                    };
                }else{
                    dataText.push(dataString);
                    acceptCount++;
                };
            };     
            count++;
        };
        if (acceptCount > 0){
            dateLabel.setAttribute("class","text-secondary");
            dateLabel.innerHTML = `В нужном диапазоне дат ${acceptCount} строк из ${strings.length-1}`;
            sendButton.hidden = false;
        }else{
            dateLabel.setAttribute("class","text-danger");
            dateLabel.innerHTML = `Ни одна строка не соответствует нужному диапазону дат !`;
        };  
    };
};


fileInput.addEventListener('change', () => {
    // извлекаем File
    file = fileInput.files[0];
    sendButton.hidden = true;
    fileLabel.innerHTML = '';
    dateLabel.innerHTML = '';
    // нас интересует то, что находится до слеша
    if (file.type.replace(/\/.+/, '') === 'text') {
        readButton.removeAttribute("disabled");
    }else{
        readButton.setAttribute("disabled", "disabled");
        fileLabel.setAttribute("class","text-danger");
        fileLabel.innerHTML = `Неверный формат файла !`;
    };
});


readButton.addEventListener("click", ()=> {
    const file = fileInput.files[0];
    if(file){
        readFile(file);
    }else{
        fileLabel.setAttribute("class","text-danger");
        fileLabel.innerHTML = `Файл не выбран !`;
    };
});

sendButton.addEventListener("click", async ()=>{
    if (dataText){
        const result = confirm("Вы действительно хотите отправить данные на сервер ?");
        if (result) {
            let count = 1;
            for (ind in dataText){
                let serverResponse = await sendString(dataText[ind]);
                resultLabel.innerHTML=`${count} из ${dataText.length}`;
                console.log(serverResponse['status'])
                count++;
            };
        };
    }else{
        alert('Почему-то нечего отправлять !');
        sendButton.hidden = true;
    };
});
