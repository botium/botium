function htmlEntities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

$(document).ready(function () {

    function getTime(){
     var dt = new Date();
       var h =  dt.getHours(), m = dt.getMinutes();
       var stime = (h > 12) ? (h-12 + ':' + m +' PM') : (h + ':' + m +' AM');
        return stime;
    }

    function scrollToBottom() {
        $(".chat")[0].scrollTop = $(".chat")[0].scrollHeight;
    }

    var put_text = function (bot_say) {
        $(".payloadPreview")[0].innerHTML = htmlEntities(JSON.stringify(bot_say, null, 4));

        if (bot_say["messages"].length > 0) {
            var id = "id" + Math.random().toString(36).substr(2, 9);
            html_data = '<li class="left clearfix"' + " id=" + id + '><div class="chat-body clearfix"><strong class="primary-font">Bot</strong>'
            for (s in bot_say["messages"]){
                message = bot_say["messages"][s];
                message_text = htmlEntities(message["text"]);
                html_data = html_data +'<p class="botsays">'+ message_text + '</p>';
            }
            html_data += '</div></li>';

            $("ul.chat").append(html_data);

            for (var i in message["options"]) {
                var text = message["options"][i];
                var $something = $('<button>')
                    .attr({ class:'btn button', value: text})
                    .text(text)
                    .click(function(clicked_id) {
                        $("ul.chat").append(user_text(this.value));
                        send_req(this.value);
                    });

                $("#quick_replies").append($something);
            }

        }
        scrollToBottom();
    };

    var send_req = function (text) {
		$('#quick_replies').empty();

		scrollToBottom();

		setTimeout(function() {
            payload = {"text": text};
            $.ajax({
                url: '/api',
                type: 'POST',
                data: JSON.stringify(payload),
                contentType: 'application/json; charset=utf-8',
                datatype: "json",
                success: successRoutes,
                error: errorRoutes,
            });
        }, 400);
        return true;
    };


    successRoutes = function (response) {
        var responseObject;
        if (typeof response == 'object') {
           responseObject= response;
        }
        else {

            var parsedResponse = JSON.parse(response);
            responseObject = parsedResponse.responseData;
        }
        put_text(responseObject);
    };

    errorRoutes = function (x, t, m) {
        responseObject = {"messages": [{'text': "sorry, API is not responding, check if it is still running"}]}
        put_text(responseObject);
    };


    function user_text(text) {
        return '<li class="right clearfix"><div class="chat-body clearfix"><strong class="primary-font">You</strong>' +
        '<p class="usersays">' + text + '</p> </div></li>';
    }

    function append_user_text(){
        if ($("#btn-input").val()){
            userQuery = $("#btn-input").val();
            $("#btn-input").val("");
            $("ul.chat").append(user_text(userQuery));
            send_req(userQuery);
        }

    }

    $('#btn-input').keydown(function (e) {
        if (e.keyCode == 13) {
            append_user_text()
        }
    })

    $('#btn-chat').click(function () {
        append_user_text()
    })


});