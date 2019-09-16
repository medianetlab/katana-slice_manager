// Code structure:
//   - Global vars, initialization
//   - Document ready           (jQuery)
//   - handlebars.js            (html templating)
//   - modal windows handling   (pop-up windows)
//   - WIM CRUD functions       (ajax)
//   - helper functions         (validation,time, etc...)



//=======================================  Global vars, initialization  ====================================//

// handlebars template for wim-table
var source   = $("#wim-table").html();
var template = Handlebars.compile(source);

// json object with all wim details
var wim_all = null;

// codemirror initialization
var cm = CodeMirror(document.getElementById('modal-textarea'),{
    lineNumbers: true,
    mode: 'javascript',
    autoRefresh: true
});

// json object with data from wim opened for editing
wim_being_edited = null;
// json object with data from wim that is about to be added
wim_being_added = null;

// global settings for toastr js (plugin for popup messages)
toastr.options.closeButton = true;
toastr.options.progressBar = true;




//=======================================  Document ready  ====================================//


$(document).ready(function(){

    // load data and add table with wim details
    render_wim_table();

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


// requests wim data from katana-mngr
// and generates the wim table template with handlebars.js
//
function render_wim_table() {

    $('.lds-wim-table').css('display', 'inline-block');

    // try to fetch the json with wim data
    $.ajax({
        type: 'GET',
        url: '/mngr/api/wim/all',
        timeout: 15000,
        dataType: 'json'
    }).fail(function(err) {
        console.log(err);
        toastr.error("Failed to load Wim data from katana-mngr.", "Error");
    }).done(function(data) {
        // generate human-readable "created at" dates from unix epoch values
        wim_all = generate_UTC_dates(data);

        var html    = template(data);
        $('.wim-table-tpl').html(html);
        $('.lds-wim-table').css('display', 'none');
    });
}




//=======================================  modal windows handling  ====================================//


// Handling of codemirror when the "inspect modal" is shown/hidden.
//   - when the modal is shown, the wim info must be fetched and added to codemirror
//   - when the modal is hidden, the wim info is removed from codemirror
//
function add_inpect_modal_event_handling() { 
    $('#inspect-modal').on('shown.bs.modal', function (event) {
        var button = $(event.relatedTarget)
        var uuid = button.parent().data('uuid')
        var name = button.parent().data('name')
        var modal = $(this)

        // add the name to the title
        modal.find('.modal-title').text('Inspect ' + name)

        // load wim details from the api
        $.ajax({
            url: '/mngr/api/wim/'+uuid,
            type: 'GET',
            dataType: 'json',
            timeout: 15000
        }).done(function(data) {
            // console.log(data);
            // add wim details to codemirror
            cm.getDoc().setValue(JSON.stringify(data, null, 4));
            cm.getDoc().setCursor({line:0,ch: 0});
        }).fail(function(err) {
            toastr.error("Failed to load Wim details from katana-mngr.", "Error");
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
        modal.find('.btn-rm-proceed').attr('data-wim-uuid',uuid);      
    })
}
function add_delete_button_listener() {
    $('.btn-rm-proceed').on('click',function(){
        $('#delete-modal').modal('hide');
        rm_wim($(this).attr('data-wim-uuid'));
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

        // load wim details from the api
        $.ajax({
            url: '/mngr/api/wim/'+uuid,
            type: 'GET',
            dataType: 'json',
            timeout: 15000
        }).done(function(data) {
            wim_being_edited = data;
            modal.find('#edit-description').val(data.description);
            modal.find('#edit-type').val(data.type);
            modal.find('#edit-location').val(data.location);
            modal.find('#edit-version').val(data.version);
        }).fail(function(err) {
            toastr.error("Failed to load Wim details from katana-mngr.", "Error");
        });       

        modal.find('.btn-edit-proceed').attr('data-wim-uuid',uuid);      
    })
}
function add_save_edit_button_listener() {
    $('.btn-edit-proceed').on('click',function(){
        // collect edited data
        wim_being_edited.name        = $('#edit-name').val();
        wim_being_edited.description = $('#edit-description').val();
        $('#edit-modal').modal('hide');
        
        update_wim(wim_being_edited._id, wim_being_edited);
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
        wim_being_added = tryParseJSON(e.target.result);
        if (!wim_being_added) {
            // if it is not JSON, try to parse it as YAML
            wim_being_added = tryParseYAML(e.target.result);
            // if it is not YAML
            if (!wim_being_added) {
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
        add_wim(wim_being_added);
        document.getElementById("file-input").value = "";
        $('.file-name').text('Drop your file here or click in this area');
        $('.btn-add-proceed').attr('disabled',true);
    });
}


//=======================================  WIM CRUD functions  ====================================//


// sends a DELETE request to the .../wim/<id> endpoint
// to remove the wim specified by the <id>
function rm_wim(uuid) {
    $.ajax({
        url: '/mngr/api/wim/'+uuid,
        type: 'DELETE',
        dataType: 'text',
        timeout: 15000,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRF-TOKEN', $.cookie('csrf_access_token'));
        }
    }).done(function(data) {
        // console.log(data);
        toastr.success("Wim has been removed successfully");
        $('.wim-trow-'+uuid).remove();
    }).fail(function(err) {
        toastr.error("Failed to remove Wim from katana-mngr", "Error");
    });
}


// sends a PUT request to the .../wim/<id> endpoint
// to update the wim specified by the <id>
function update_wim(uuid, data) {
    $.ajax({
        url: '/mngr/api/wim/'+uuid,
        type: 'PUT',
        contentType : 'application/json',
        timeout: 15000,
        data: JSON.stringify(data),
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRF-TOKEN', $.cookie('csrf_access_token'));
        }
    }).done(function(data) {
        console.log(data);
        toastr.success("Wim has been updated successfully");
        render_wim_table();
    }).fail(function(err) {
        toastr.error("Failed to update Wim from katana-mngr", "Error");
    });
}



// sends a POST request to the .../wim/ endpoint
// to add a new wim with the specs (data) provided
function add_wim(data) {
    $.ajax({
        url: '/mngr/api/wim',
        type: 'POST',
        contentType : 'application/json',
        timeout: 15000,
        data: JSON.stringify(data),
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRF-TOKEN', $.cookie('csrf_access_token'));
        }
    }).done(function(data) {
        toastr.success("Wim has been added successfully");
        render_wim_table();
    }).fail(function(err) {
        toastr.error("Failed to add Wim to katana-mngr", "Error");
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
