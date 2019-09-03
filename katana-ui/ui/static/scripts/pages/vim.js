// json object with all vim details
var vim_all = null;

// codemirror initialization
var cm = CodeMirror(document.getElementById('modal-textarea'),{
    lineNumbers: true,
    mode: 'javascript',
    autoRefresh: true
});




//=======================================  Document ready  ====================================//

$(document).ready(function(){

    // global settings for toastr js (plugin for popup messages)
    toastr.options.closeButton = true;
    toastr.options.progressBar = true;

    // load data and add table with vim details
    render_vim_table();

    // handle what happens when the "inspect modal" is shown/hidden
    add_inpect_modal_event_handling();

    
});






//=======================================  helper functions  ====================================//

function render_vim_table() {
    // template for vim-table
    var source   = $("#vim-table").html();
    var template = Handlebars.compile(source);

    // try to fetch the json with vim data
    $.ajax({
        type: 'GET',
        url: '/mngr/api/vim/all',
        timeout: 15000,

        error: function(err)
        {
            console.log(err);
            toastr.error(err.status + " " + err.statusText,"GET /mngr/api/vim/all error");
        },
        dataType: 'json',
        success: function(data) {
            // console.log(data);
            vim_all = data;
            var html    = template(data);
            $('.vim-table-tpl').html(html);

            // if the template is rendered and the table is added to the page
            // add listeners
            add_vim_button_group_listeners();

        }
    });
}



function add_vim_button_group_listeners() {
    // remove button
    $('.btn-rm').on('click', function(){
       rm_vim(($(this).parent().attr('data-uuid')))        
    });
}



// sends a DELETE request to the .../vim/<id> endpoint
// to remove the vim specified by the <id>
function rm_vim(uuid) {
    $.ajax({
        url: '/mngr/api/vim/'+uuid,
        type: 'DELETE',
        dataType: 'text',
        timeout: 15000
    }).done(function(data) {
        // console.log(data);
        toastr.success("Vim has been removed successfully");
        $('.vim-trow-'+uuid).remove();
    }).fail(function() {
        console.log(err);
        toastr.error(err.status + " " + err.statusText,"DELETE /mngr/api/vim/{id} error");
    });
}



// Handling of codemirror when the "inspect modal" is shown/hidden.
//   - when the modal is shown, the vim info must be fetched and added to codemirror
//   - when the modal is hidden, the vim info is removed from codemirror
//
function add_inpect_modal_event_handling() { 
    $('#inspect-modal').on('shown.bs.modal', function (event) {
        var button = $(event.relatedTarget)
        var uuid = button.parent().data('uuid')
        var name = button.parent().data('name')
        var modal = $(this)

        // add the name to the title
        modal.find('.modal-title').text('Inspect ' + name)

        // load vim details from the api
        $.ajax({
            url: '/mngr/api/vim/'+uuid,
            type: 'GET',
            dataType: 'json',
            timeout: 15000
        }).done(function(data) {
            // console.log(data);
            // add vim details to codemirror
            cm.getDoc().setValue(JSON.stringify(data, null, 4));
            cm.getDoc().setCursor({line:0,ch: 0});
        }).fail(function() {
            console.log(err);
            toastr.error(err.status + " " + err.statusText,"DELETE /mngr/api/vim/{id} error");
        });
      
    })

    $('#inspect-modal').on('hidden.bs.modal', function (event) {
        // delete previous codemirror content/history
        cm.getDoc().setValue("");
    });
}