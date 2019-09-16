/*!
 * jQuery Cookie Plugin v1.4.1
 * https://github.com/carhartl/jquery-cookie
 */
!function(e){"function"==typeof define&&define.amd?define(["jquery"],e):"object"==typeof exports?module.exports=e(require("jquery")):e(jQuery)}(function(e){function n(e){return u.raw?e:encodeURIComponent(e)}function o(e){return u.raw?e:decodeURIComponent(e)}function i(e){return n(u.json?JSON.stringify(e):String(e))}function t(e){0===e.indexOf('"')&&(e=e.slice(1,-1).replace(/\\"/g,'"').replace(/\\\\/g,"\\"));try{return e=decodeURIComponent(e.replace(c," ")),u.json?JSON.parse(e):e}catch(e){}}function r(n,o){var i=u.raw?n:t(n);return e.isFunction(o)?o(i):i}var c=/\+/g,u=e.cookie=function(t,c,s){if(arguments.length>1&&!e.isFunction(c)){if("number"==typeof(s=e.extend({},u.defaults,s)).expires){var d=s.expires,f=s.expires=new Date;f.setMilliseconds(f.getMilliseconds()+864e5*d)}return document.cookie=[n(t),"=",i(c),s.expires?"; expires="+s.expires.toUTCString():"",s.path?"; path="+s.path:"",s.domain?"; domain="+s.domain:"",s.secure?"; secure":""].join("")}for(var a=t?void 0:{},p=document.cookie?document.cookie.split("; "):[],l=0,m=p.length;l<m;l++){var x=p[l].split("="),g=o(x.shift()),j=x.join("=");if(t===g){a=r(j,c);break}t||void 0===(j=r(j))||(a[g]=j)}return a};u.defaults={},e.removeCookie=function(n,o){return e.cookie(n,"",e.extend({},o,{expires:-1})),!e.cookie(n)}});

// Main code

var signup = function () {
  var $signup = $('#signup');

  $signup.on('submit', function(event) {
    event.preventDefault();

    var url = $signup.attr('action');
    var redirect = $('#signup-link').data('next');
    var $email = $('#email');
    var $username = $('#username');
    var $password = $('#password');
    var $error = $('#form_error');

    var data = {
      'email': $email.val(),
      'username': $username.val(),
      'password': $password.val()
    }

    return $.ajax({
      type: 'post',
      url: url,
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify(data),
      processData: false,
      success: function(response, status, xhr) {
        $error.hide();
        window.location.replace(redirect);
      },
      error: function(response, status, xhr) {
        $error.text(response.responseText);
        $error.show();
      }
    });
  });
};

var login = function () {
  var $login = $('#login');

  $login.on('submit', function(event) {
    event.preventDefault();

    var url = $login.attr('action');
    var redirect = $('#login-link').data('next');
    var $identity = $('#identity');
    var $password = $('#password');
    var $error = $('#form_error');

    var data = {
      'identity': $identity.val(),
      'password': $password.val()
    }

    return $.ajax({
      type: 'post',
      url: url,
      dataType: 'json',
      contentType: 'application/json',
      data: JSON.stringify(data),
      processData: false,
      success: function(response, status, xhr) {
        window.location.replace(redirect);
      },
      error: function(response, status, xhr) {
        $error.text(response.responseText);
        $error.show();
      }
    });
  });
};

var logout = function () {
  var $logoutLink = $('#logout-link');

  $logoutLink.on('click', function(event) {
    event.preventDefault();

    var url = $logoutLink.attr('href');
    var redirect = $logoutLink.data('next');

    return $.ajax({
      type: 'delete',
      url: url,
      dataType: 'json',
      contentType: 'application/json',
      processData: false,
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRF-TOKEN', $.cookie('csrf_access_token'));
      },
      success: function(response, status, xhr) {
        window.location.replace(redirect);
      }
    });
  });
}

var navstate = function () {
  var cookie_name = 'csrf_access_token';
  var $noauth = $('.nav-noauth');
  var $withauth = $('.nav-withauth');

  if ($.cookie(cookie_name)) {
    $noauth.hide();
    $withauth.show();
  } else {
    $withauth.hide();
    $noauth.show();
  }

  return true;
};

// Initialize everything when the DOM is ready.
$(document).ready(function() {
  navstate();

  signup();
  login();
  logout();
});
