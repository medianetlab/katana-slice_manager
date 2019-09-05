//=======================================  Global vars, initialization  ====================================//

// handlebars template for vim-table
var source   = $("#vim-table").html();
var template = Handlebars.compile(source);

// json object with all vim details
var vim_all = null;

// codemirror initialization
var cm = CodeMirror(document.getElementById('modal-textarea'),{
    lineNumbers: true,
    mode: 'javascript',
    autoRefresh: true
});

// json object with data from vim opened for editing
vim_being_edited = null;




//=======================================  Document ready  ====================================//


$(document).ready(function(){

    // global settings for toastr js (plugin for popup messages)
    toastr.options.closeButton = true;
    toastr.options.progressBar = true;

    // load data and add table with vim details
    render_vim_table();

    // handle what happens when the "inspect modal" is shown/hidden
    add_inpect_modal_event_handling();

    // handle what happens when the "delete modal" is shown/hidden
    // and the delete button is pressed
    add_delete_modal_event_handling();
    add_delete_button_listener();

    // handle what happens when the "edit modal" is shown/hidden
    // and the save button is pressed
    add_edit_modal_event_handling();
    add_save_edit_button_listener();
});




//=======================================  handlebars.js  ====================================//


// requests vim data from katana-mngr
// and generates the vim table template with handlebars.js
//
function render_vim_table() {

    $('.lds-vim-table').css('display', 'inline-block');

    // try to fetch the json with vim data
    $.ajax({
        type: 'GET',
        url: '/mngr/api/vim/all',
        timeout: 15000,
        dataType: 'json'
    }).fail(function(err) {
        console.log(err);
        toastr.error("Failed to load Vim data from katana-mngr.", "Error");
    }).done(function(data) {
        // generate human-readable "created at" dates from unix epoch values
        vim_all = generate_UTC_dates(data);

        var html    = template(data);
        $('.vim-table-tpl').html(html);
        $('.lds-vim-table').css('display', 'none');
    });
}




//=======================================  modal windows handling  ====================================//


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
        }).fail(function(err) {
            toastr.error("Failed to load Vim details from katana-mngr.", "Error");
        });
      
    })

    $('#inspect-modal').on('hidden.bs.modal', function (event) {
        // delete previous codemirror content/history
        cm.getDoc().setValue("");
    });
}



function add_delete_modal_event_handling() {
    $('#delete-modal').on('shown.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var uuid = button.parent().data('uuid');
        var name = button.parent().data('name');
        var modal = $(this);

        // add the name to the title/question
        modal.find('.modal-title').text('Delete ' + name);
        modal.find('.modal-text').text('Are you sure you want to delete '+ name + '?');
        modal.find('.btn-rm-proceed').attr('data-vim-uuid',uuid);      
    })
}
function add_delete_button_listener() {
    $('.btn-rm-proceed').on('click',function(){
        $('#delete-modal').modal('hide');
        rm_vim($(this).attr('data-vim-uuid'));
    });
}



function add_edit_modal_event_handling() {
    $('#edit-modal').on('shown.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var uuid = button.parent().data('uuid');
        var name = button.parent().data('name');
        var modal = $(this);

        // add the name to the title
        modal.find('.modal-title').text('Edit ' + name);
        modal.find('#edit-name').val(name);

        // load vim details from the api
        $.ajax({
            url: '/mngr/api/vim/'+uuid,
            type: 'GET',
            dataType: 'json',
            timeout: 15000
        }).done(function(data) {
            vim_being_edited = data;
            modal.find('#edit-description').val(data.description);
            modal.find('#edit-type').val(data.type);
            modal.find('#edit-location').val(data.location);
            modal.find('#edit-version').val(data.version);
        }).fail(function(err) {
            toastr.error("Failed to load Vim details from katana-mngr.", "Error");
        });       

        modal.find('.btn-edit-proceed').attr('data-vim-uuid',uuid);      
    })
}
function add_save_edit_button_listener() {
    $('.btn-edit-proceed').on('click',function(){
        // collect edited data
        vim_being_edited.name        = $('#edit-name').val();
        vim_being_edited.description = $('#edit-description').val();
        vim_being_edited.type        = $('#edit-type').val();
        vim_being_edited.location    = $('#edit-location').val();
        vim_being_edited.version     = $('#edit-version').val();
        $('#edit-modal').modal('hide');
        
        update_vim(vim_being_edited._id, vim_being_edited);
    });
}




//=======================================  helper functions  ====================================//


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
    }).fail(function(err) {
        toastr.error("Failed to remove Vim from katana-mngr.", "Error");
    });
}


// sends a PUT request to the .../vim/<id> endpoint
// to update the vim specified by the <id>
function update_vim(uuid, data) {
    $.ajax({
        url: '/mngr/api/vim/'+uuid,
        type: 'PUT',
        contentType : 'application/json',
        timeout: 15000,
        data: JSON.stringify(data),
    }).done(function(data) {
        console.log(data);
        toastr.success("Vim has been updated successfully");
        render_vim_table();
    }).fail(function(err) {
        toastr.error("Failed to update Vim from katana-mngr.", "Error");
    });
}


// "created_at" values are floating point numbers generated from Python time.time()
// this function generates "created_at_UTC", a human readable version of the above
function generate_UTC_dates(data) {
    data.forEach(function(entry) {
        date = new Date(entry.created_at*1000);
        entry.created_at_UTC = date.toUTCString();
    });
    return data;
}