$(document).ready(function(){

    // global settings for toastr js (plugin for popup messages)
    toastr.options.closeButton = true;
    toastr.options.progressBar = true;

    render_vim_table();

});


function render_vim_table() {
    // template for vim-table
    var source   = $("#vim-table").html();
    var template = Handlebars.compile(source);

    // try to fetch the json with vim data
    $.ajax({
        type: 'GET',
        url: '/api/vim/all',
        timeout: 15000,

        error: function(err)
        {
            console.log(err);
            toastr.error(err.status + " " + err.statusText,"GET /api/vim/all error");
        },
        dataType: 'json',
        success: function(data) {
            // console.log(data);
            var html    = template(data);
            $('.vim-table-tpl').html(html);

            // if the template is rendered and the table is added to the page
            // add listeners
            add_vim_button_group_listeners();

        }
    });
}


function add_vim_button_group_listeners() {
    $('.btn-rm').on('click', function(){
       rm_vim(($(this).parent().attr('data-uuid')))        
    });
}


function rm_vim(uuid) {
    $.ajax({
        type: 'DELETE',
        url: '/api/vim/'+uuid,
        timeout: 15000,

        error: function(err)
        {
            console.log(err);
            toastr.error(err.status + " " + err.statusText,"DELETE /api/vim/<uuid> error");
        },
        dataType: 'json',
        success: function(data) {
            console.log(data);
            toastr.success("Vim has been removed successfully");
            $('.vim-trow-'+uuid).remove();
        }
    });
}