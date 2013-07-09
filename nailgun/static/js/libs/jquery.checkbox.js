/**
 * jQuery custom checkboxes
 *
 * Copyright (c) 2008 Khavilo Dmitry (http://widowmaker.kiev.ua/checkbox/)
 * Licensed under the MIT License:
 * http://www.opensource.org/licenses/mit-license.php
 *
 * @version 1.3.0 Beta 1
 * @author Khavilo Dmitry
 * @mailto wm.morgun@gmail.com
**/

(function($){
	var CB = function(e)
	{
		if (!e) var e = window.event;
		e.cancelBubble = true;
		if (e.stopPropagation) e.stopPropagation();
	};
	$.fn.checkbox = function(options) {
		var addEvents = function(object)
		{
			var checked = object.checked;
			var disabled = object.disabled;
			var $object = $(object);

			if ( object.stateInterval )
				clearInterval(object.stateInterval);

			object.stateInterval = setInterval(
				function()
				{
					if ( object.disabled != disabled )
						$object.trigger( (disabled = !!object.disabled) ? 'disable' : 'enable');
					if ( object.checked != checked )
						$object.trigger( (checked = !!object.checked) ? 'check' : 'uncheck');
				},
				10
			);
			return $object;
		};
		return this.each(function()
		{
			var ch = this;
			var $ch = addEvents(ch);
			if (ch.wrapper) ch.wrapper.remove();
			ch.wrapper = $('<span>&nbsp;</span>');
			$ch.after(ch.wrapper);
			ch.wrapper.click(function(e) { $ch.trigger('click',[e]); CB(e); return false;});
			$ch.click(function(e){CB(e);});
			$ch.bind('check', function() { ch.wrapper.addClass('checked' );}).bind('uncheck', function() { ch.wrapper.removeClass('checked');});
			if ( ch.checked ) ch.wrapper.addClass('checked');
		});
	}
})(jQuery);
