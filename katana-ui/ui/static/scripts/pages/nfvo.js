// Code structure:
//   - Global vars, initialization
//   - Document ready           (jQuery)
//   - handlebars.js            (html templating)
//   - modal windows handling   (pop-up windows)
//   - NFVO CRUD functions       (ajax)
//   - helper functions         (validation,time, etc...)



//=======================================  Global vars, initialization  ====================================//

// handlebars template for nfvo-table
var source   = $("#nfvo-table").html();
var template = Handlebars.compile(source);

// json object with all nfvo details
var nfvo_all = null;

// codemirror initialization
var cm = CodeMirror(document.getElementById('modal-textarea'),{
    lineNumbers: true,
    mode: 'javascript',
    autoRefresh: true
});

// json object with data from nfvo opened for editing
nfvo_being_edited = null;
// json object with data from nfvo that is about to be added
nfvo_being_added = null;

// global settings for toastr js (plugin for popup messages)
toastr.options.closeButton = true;
toastr.options.progressBar = true;




//=======================================  Document ready  ====================================//


$(document).ready(function(){

    // load data and add table with nfvo details
    render_nfvo_table();

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

    // handle what happens when the "add modal" is shown/hidden
    // a file is selected
    // and the submit button is pressed
    add_add_modal_event_handling();
    add_file_input_event_handling();
    add_submit_button_listener();
});




//=======================================  handlebars.js  ====================================//


// requests nfvo data from katana-mngr
// and generates the nfvo table template with handlebars.js
//
function render_nfvo_table() {

    $('.lds-nfvo-table').css('display', 'inline-block');

    // try to fetch the json with nfvo data
    $.ajax({
        type: 'GET',
        url: '/mngr/api/nfvo/all',
        timeout: 15000,
        dataType: 'json'
    }).fail(function(err) {
        console.log(err);
        toastr.error("Failed to load NFVO data from katana-mngr.", "Error");
    }).done(function(data) {
        // generate human-readable "created at" dates from unix epoch values
        nfvo_all = generate_UTC_dates(data);

        var html    = template(data);
        $('.nfvo-table-tpl').html(html);
        $('.lds-nfvo-table').css('display', 'none');
    });
}




//=======================================  modal windows handling  ====================================//


// Handling of codemirror when the "inspect modal" is shown/hidden.
//   - when the modal is shown, the nfvo info must be fetched and added to codemirror
//   - when the modal is hidden, the nfvo info is removed from codemirror
//
function add_inpect_modal_event_handling() { 
    $('#inspect-modal').on('shown.bs.modal', function (event) {
        var button = $(event.relatedTarget)
        var uuid = button.parent().data('uuid')
        var name = button.parent().data('name')
        var modal = $(this)

        // add the name to the title
        modal.find('.modal-title').text('Inspect ' + name)

        // load nfvo details from the api
        $.ajax({
            url: '/mngr/api/nfvo/'+uuid,
            type: 'GET',
            dataType: 'json',
            timeout: 15000
        }).done(function(data) {
            // console.log(data);
            // add nfvo details to codemirror
            cm.getDoc().setValue(JSON.stringify(data, null, 4));
            cm.getDoc().setCursor({line:0,ch: 0});
        }).fail(function(err) {
            toastr.error("Failed to load NFVO details from katana-mngr.", "Error");
        });
      
    })

    $('#inspect-modal').on('hidden.bs.modal', function (event) {
        // delete previous codemirror content/history
        cm.getDoc().setValue("");
    });
}



// Handling of delete modal show/hide and delete button click
//
function add_delete_modal_event_handling() {
    $('#delete-modal').on('shown.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var uuid = button.parent().data('uuid');
        var name = button.parent().data('name');
        var modal = $(this);

        // add the name to the title/question
        modal.find('.modal-title').text('Delete ' + name);
        modal.find('.modal-text').text('Are you sure you want to delete '+ name + '?');
        modal.find('.btn-rm-proceed').attr('data-nfvo-uuid',uuid);      
    })
}
function add_delete_button_listener() {
    $('.btn-rm-proceed').on('click',function(){
        $('#delete-modal').modal('hide');
        rm_nfvo($(this).attr('data-nfvo-uuid'));
    });
}



// Handling of edit modal show/hide and save button click
//
function add_edit_modal_event_handling() {
    $('#edit-modal').on('shown.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var uuid = button.parent().data('uuid');
        var name = button.parent().data('name');
        var modal = $(this);

        // add the name to the title
        modal.find('.modal-title').text('Edit ' + name);
        modal.find('#edit-name').val(name);

        // load nfvo details from the api
        $.ajax({
            url: '/mngr/api/nfvo/'+uuid,
            type: 'GET',
            dataType: 'json',
            timeout: 15000
        }).done(function(data) {
            nfvo_being_edited = data;
            modal.find('#edit-description').val(data.description);
            modal.find('#edit-type').val(data.type);
            modal.find('#edit-location').val(data.location);
            modal.find('#edit-version').val(data.version);
        }).fail(function(err) {
            toastr.error("Failed to load NFVO details from katana-mngr.", "Error");
        });       

        modal.find('.btn-edit-proceed').attr('data-nfvo-uuid',uuid);      
    })
}
function add_save_edit_button_listener() {
    $('.btn-edit-proceed').on('click',function(){
        // collect edited data
        nfvo_being_edited.name        = $('#edit-name').val();
        nfvo_being_edited.description = $('#edit-description').val();
        nfvo_being_edited.type        = $('#edit-type').val();
        nfvo_being_edited.location    = $('#edit-location').val();
        nfvo_being_edited.version     = $('#edit-version').val();
        $('#edit-modal').modal('hide');
        
        update_nfvo(nfvo_being_edited._id, nfvo_being_edited);
    });
}




// Handling of add modal show/hide and submit button click
//
function add_add_modal_event_handling() {
    $('#add-modal').on('shown.bs.modal', function (event) {
        //
    })
}
function add_file_input_event_handling() {
    $('#file-input').on('change',function(event){

        var file = event.target.files[0];
                  
        if (!file) {
            $('.file-name').text('Drop your file here or click in this area');
            $('.btn-add-proceed').attr('disabled',true);
            return;
        }
        $('.file-name').text(file.name);

        // read the file without uploading it to the server
        var reader = new FileReader();
        reader.onload = function(e) {
        // try to parse it as JSON
        nfvo_being_added = tryParseJSON(e.target.result);
        if (!nfvo_being_added) {
            // if it is not JSON, try to parse it as YAML
            nfvo_being_added = tryParseYAML(e.target.result);
            // if it is not YAML
            if (!nfvo_being_added) {
                $('.btn-add-proceed').attr('disabled',true);
                toastr.error("No valid json or yaml data, failed to parse file content", "Error");
                document.getElementById("file-input").value = "";
                $('.file-name').text('Drop your file here or click in this area');
            } else {
                $('.btn-add-proceed').attr('disabled',false);
            }
        } else {
            $('.btn-add-proceed').attr('disabled',false);
        }
        };
        reader.readAsText(file);
    });

    // add "dragging" class when needed
    $('#file-input').on("dragover", function(event) {
        event.preventDefault();  
        event.stopPropagation();
        $(this).parent().addClass('dragging');
    });
    $('#file-input').on("dragleave", function(event) {
        event.preventDefault();  
        event.stopPropagation();
        $(this).parent().removeClass('dragging');
    });
    $('#file-input').on("drop", function(event) {
        $(this).parent().removeClass('dragging');
    });
}
function add_submit_button_listener() {
    $('.btn-add-proceed').on('click',function(){
        $('#add-modal').modal('hide');
        add_nfvo(nfvo_being_added);
        document.getElementById("file-input").value = "";
        $('.file-name').text('Drop your file here or click in this area');
        $('.btn-add-proceed').attr('disabled',true);
    });
}


//=======================================  NFVO CRUD functions  ====================================//


// sends a DELETE request to the .../nfvo/<id> endpoint
// to remove the nfvo specified by the <id>
function rm_nfvo(uuid) {
    $.ajax({
        url: '/mngr/api/nfvo/'+uuid,
        type: 'DELETE',
        dataType: 'text',
        timeout: 15000,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRF-TOKEN', $.cookie('csrf_access_token'));
        }
    }).done(function(data) {
        // console.log(data);
        toastr.success("NFVO has been removed successfully");
        $('.nfvo-trow-'+uuid).remove();
    }).fail(function(err) {
        toastr.error("Failed to remove NFVO from katana-mngr", "Error");
    });
}


// sends a PUT request to the .../nfvo/<id> endpoint
// to update the nfvo specified by the <id>
function update_nfvo(uuid, data) {
    $.ajax({
        url: '/mngr/api/nfvo/'+uuid,
        type: 'PUT',
        contentType : 'application/json',
        timeout: 15000,
        data: JSON.stringify(data),
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRF-TOKEN', $.cookie('csrf_access_token'));
        }
    }).done(function(data) {
        console.log(data);
        toastr.success("NFVO has been updated successfully");
        render_nfvo_table();
    }).fail(function(err) {
        toastr.error("Failed to update NFVO from katana-mngr", "Error");
    });
}



// sends a POST request to the .../nfvo/ endpoint
// to add a new nfvo with the specs (data) provided
function add_nfvo(data) {
    $.ajax({
        url: '/mngr/api/nfvo',
        type: 'POST',
        contentType : 'application/json',
        timeout: 15000,
        data: JSON.stringify(data),
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRF-TOKEN', $.cookie('csrf_access_token'));
        }
    }).done(function(data) {
        toastr.success("NFVO has been added successfully");
        render_nfvo_table();
    }).fail(function(err) {
        toastr.error("Failed to add NFVO to katana-mngr", "Error");
    });
}





//=======================================  helper functions  ====================================//


// "created_at" values are floating point numbers generated from Python time.time()
// this function generates "created_at_UTC", a human readable version of the above
function generate_UTC_dates(data) {
    data.forEach(function(entry) {
        date = new Date(entry.created_at*1000);
        entry.created_at_UTC = date.toUTCString();
    });
    return data;
}


// from: https://stackoverflow.com/questions/3710204
function tryParseJSON (jsonString){
    try {
        var o = JSON.parse(jsonString);

        // Handle non-exception-throwing cases:
        // Neither JSON.parse(false) or JSON.parse(1234) throw errors, hence the type-checking,
        // but... JSON.parse(null) returns null, and typeof null === "object",
        // so we must check for that, too. Thankfully, null is falsey, so this suffices:
        if (o && typeof o === "object") {
            return o;
        }
    }
    catch (e) { }

    return false;
};

function tryParseYAML(yamlString) {
    try {
        var o = jsyaml.load(yamlString);

        if (o && typeof o === "object") {
            return o;
        }
    }
    catch (e) { }
    
    return false;
}
