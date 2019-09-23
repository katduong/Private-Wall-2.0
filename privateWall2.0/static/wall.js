$(document).ready(function() {

    console.log("hello")
    $('.delete').on('click', function(){
        var id = $(this).attr('id').substr(6);
        console.log(id);
        var deleteId = id.substr(6);
        var route = "/delete/" + id;
        var strid = "#" + id
        console.log(route);
        $.ajax({
            method: "GET",
            url: route
        })
        .done(function(res){
            console.log("response: " + res)
            $("#numMessages").html(res)
            $(strid).remove()
        })
        return false;
    })

    $(document).on("submit", ".send", function(e){
        e.preventDefault();
        var id = $(this).attr('id').substr(4);
        console.log(data);
        var selector = "#send" + id;
        var data = $(selector).serialize();
        $.ajax({
            method: "POST",
            url: "/sendMessage",
            data: data
        })
        .done(function(res){
            console.log("response: " + res)
            // $("#messagesSent").html(res)
            $("#sendMessages").html(res)
        })
        return false;
    })
})
