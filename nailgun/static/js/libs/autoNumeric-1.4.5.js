/**
 * autoNumeric.js
 * @author: Bob Knothe
 * @version: 1.4.5
 *
 * Created by Robert J. Knothe on 2010-03-25. Please report any bug at http://www.decorplanit.com/plugin/
 *
 * Copyright (c) 2010 Robert J. Knothe  http://www.decorplanit.com/plugin/
 *
 * The MIT License (http://www.opensource.org/licenses/mit-license.php)
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */
(function($){
	$.fn.autoNumeric = function(){
		return this.each(function(){
			var d = $.extend($.fn.autoNumeric.defaults); //sets defaults
			var iv = $(this); //check input value iv
			var ii = this.id; //input ID
			var kdCode = ''; //Key down Code
			var selectLength = 0; // length of input selected
			var cPos = 0; //caret poistion
			var inLength = 0; //variable to length prior to keypress event
			var numLeft = 0;
			$(this).focus(function(e){ //start keyDown
				//$.extend(d, autoCode(ii, d)); //update defaults
			}).keydown(function(e){ //start keyDown
				if (!e){ // routine for key and character codes
					e = window.event;
				}
				if (e.keyCode){ // IE
					kdCode = e.keyCode;
				}
				else if (e.which){ // FF & O
					kdCode = e.which;
				}
				if (!kdCode) {
					//kdCode = 32;
				}
				if (document.selection){ // IE Support to find the caret position
					this.focus();
					var select = document.selection.createRange();
					selectLength = document.selection.createRange().text.length;
					select.moveStart ('character', -this.value.length);
					cPos = (select.text.length - selectLength) * 1;
				}
				else if (this.selectionStart || this.selectionStart == '0'){ // Firefox support  to find the caret position
					selectLength = this.selectionEnd * 1 - this.selectionStart * 1;
					cPos = this.selectionStart * 1;
				} // end caret position
				inLength = this.value.length; //pass length to keypress event for value left & right of the decimal position & keyUp event to set caret position
			}).keypress(function(e){ // keypress function
				//$.extend(d, autoCode(ii, d)); //update defaults
				var allowed = d.aNum + d.aSign + d.aDec; //allowed input
				var charLeft = 0; //number of characters to the left of the decimal point
				var charRight = 0; //number of characters to the right of the decimal point
				charLeft = inLength - (inLength - this.value.lastIndexOf(d.aDec)); // characters to the left of the decimal point
				if (charLeft == -1){// if no decimal point is present charLeft = inLength
					charLeft = inLength;
				}
				charRight = (inLength - this.value.lastIndexOf(d.aDec)) -1; //characters to the right of the decimal point
				if (this.value.lastIndexOf(d.aDec) == -1){ // if no decimal point charRight = 0
					charRight = 0;
				}
				numLeft = countLeft(this.value, charLeft); //the number of intergers to the left of the decimal point

				if (!e){ // routine for key and character codes
					e = window.event;
				}
				var kpCode = ''; //Key Press Code
				if (e.keyCode){ // IE
					kpCode = e.keyCode;
				}
				else if (e.which){ // FF & O
					kpCode = e.which;
				}
				if (!kpCode) {
					//kpCode = 32;
				}
				var cCode = String.fromCharCode(kpCode);	//Character code

				if ((e.ctrlKey) && (kdCode == 67 || kdCode == 86 || kdCode == 88)){ // allows controll key & copy(c=67), past (v=86), cut (v=88) or the delete key (46)
					return true;
				}
				if (kdCode == 8 || kdCode == 9 || kdCode == 35 || kdCode == 36 || kdCode == 37 || kdCode == 39 || kdCode == 46){ // allows the backspace (8), tab (9), enter 13, end (35), home(36), left(37) and right(39) arrows key to function in some browsers (FF & O)
					return true;
				}
				if (allowed.indexOf(cCode) == -1){// checks for allowed characters
					e.preventDefault();
				}
				if (cCode == d.aDec){ // start rules when the decimal charactor key is pressed **********************************************************************************
					if (selectLength == inLength && selectLength > 0){ // allows the selected input to be replaced with a number - Thanks Bart.
						return;
					}
					if (this.value.indexOf(d.aDec) != -1 || d.mDec <= 0 || cPos < this.value.length - d.mDec || cPos === 0 && this.value.charAt(0) == '-' || this.value.lastIndexOf(d.aSep) >= cPos && d.aSep !== ''){ //prevents decimal point accurcy greater then the allowed
						e.preventDefault();
					}
				}  // end rules when the decimal charactor key is pressed
				if (kpCode == 45 && (cPos > 0 || this.value.indexOf('-') != -1 || d.aSign === '')){// rules for negative key press ***********************
					e.preventDefault();
				}
				if (kpCode >= 48 && kpCode <= 57){ // start rules for number key press **********************************************************************************
					if (selectLength > 0){ // allows the selected input to be replaced with a number - Thanks Bart.
						return true;
					}
					if (this.value.indexOf('-') != -1 && cPos === 0){ // start rules for controlling a leading zero when the negative sign is present
						e.preventDefault();
					}
					if (numLeft >= d.mNum && cPos <= charLeft){ //checks for max numeric characters to the left of the decimal point
						e.preventDefault();
					}
					if (this.value.indexOf(d.aDec) != -1 && cPos >= (this.value.length - charRight) && charRight >= d.mDec){  // rules controls the maximum decimal places on both positive and negative values
						e.preventDefault();
					}
				} // end rules for number key press
			}).keyup(function(e){ //start keyup - this will format the input
				if (d.aSep === '' || e.keyCode == 9 || e.keyCode == 20 || e.keyCode == 35 || e.keyCode == 36 || e.keyCode == 37 || e.keyCode == 39 || kdCode == 9 || kdCode == 13 || kdCode == 20 || kdCode == 35 || kdCode == 36 || kdCode == 37 || kdCode == 39){// allows the tab(9), end(35), home(36) left(37) & right(39) arrows and when there is no thousand separator to bypass the autoGroup function
					return true; //kuCode 35 & 36 Home and end keys fix thanks to JPM USA
				}
				// if(kdCode == 110 && this.value.indexOf(d.aDec) == -1 && d.mDec > 0 && cPos >= this.value.length - d.mDec && this.value.lastIndexOf(d.aSep) < cPos && this.value.lastIndexOf('-') < cPos){ // start mods for period to comma on numerica pad
					// $(this).val(this.value.substring(0, cPos) + d.aDec + this.value.substring(inLength, cPos));
				// } // end mods
				$(this).val(autoGroup(this.value, d));
				//$('#' + this.id).val(autoGroup(this.value, d));
				var outLength = this.value.length;
				var outLeft = outLength - (outLength - this.value.lastIndexOf(d.aDec)); // characters to the left of the decimal point
				if (outLeft == -1){// if no decimal point is present charLeft = inLength
					outLeft = outLength;
				}
				numLeft = countLeft(this.value, outLeft); //the number of intergers to the left of the decimal point
				if (numLeft > d.mNum){
					$('#' + this.id).val('');
				}
				var setCaret = 0;
				if (inLength < outLength){
					setCaret = cPos + (outLength - inLength);
				}
				if (inLength > outLength){
					if(selectLength > 0){
						setCaret = (outLength - (inLength - (cPos + selectLength)));
					}
					else if((inLength - 2) == outLength){
						if(kdCode == 8){
							setCaret = (cPos - 2);
						}
						else{
							setCaret = (cPos - 1);
						}
					}
					else{
						if(kdCode == 8){
							setCaret = (cPos - 1);
						}
						else{
							setCaret = cPos;
						}
					}
				}
				if (inLength == outLength){
					if(this.value.charAt(cPos - 1) == d.aSep && kdCode == 8){
						setCaret = (cPos - 1);
					}
					else if(this.value.charAt(cPos) == d.aSep && kdCode == 46){
						setCaret = (cPos + 1);
					}
					else if(outLength === 1){
						setCaret = cPos + 1;
					}
					else {
						setCaret = cPos;
					}
				}
				var iField = this;
				iField.focus();
				if (document.selection) {
					var iRange = iField.createTextRange();
					iRange.collapse(true);
					iRange.moveStart("character", setCaret);
					iRange.moveEnd("character", 0);
					iRange.select();
				}
				else if (iField.selectionStart) {
					iField.selectionStart = setCaret;
					iField.selectionEnd = setCaret;
				}
			}).blur(function (){
				if ($('#' + ii).val() != ''){
					autoCheck(iv, ii, d);
				}
			});
			$(this).bind('paste', function(){setTimeout(function(){autoCheck(iv, ii, d);}, 0); }); // thanks to Josh of Digitalbush.com
		});
	};
	$.fn.autoNumeric.defaults = {
		aNum: '0123456789', //allowed  numeric values
		aSign: '', // allowed negative sign / character
		aSep: ' ', // allowed housand separator character
		aDec: '.', // allowed decimal separator character
		mNum: 15, // max number of numerical characters to the left of the decimal
		mDec: 0, // max number of decimal places
		dGroup: /(\d)((\d{3}?)+)$/, // digital grouping for the thousand separator used in Format
		rMethod: 'S' // rounding method used
	};
	function autoCode(ii, d){ // function to update the defaults settings
		if (!$('#'+ii).length) {
			return;
		}

		var fCode = $('#'+ii).attr('alt');
		var lookUp = 'dp' + fCode.charAt(5);
		if (fCode !== ''){
			d.aSign = (fCode.charAt(0) === 'n') ? '-' : ''; //Negative allowed?
			if(fCode.charAt(1) === '0'){
				d.mNum = 15;
			}
			else if(fCode.charAt(1) > '0' && fCode.charAt(1) <= '9'){
				d.mNum = fCode.charAt(1) * 1;
			}
			else{
				d.nNum = 9;
			}
			if (fCode.charAt(2) === 'a'){
				d.aSep = '\'';
			}
			else if (fCode.charAt(2) === 'p'){
				d.aSep = '.';
			}
			else if (fCode.charAt(2) === 's'){
				d.aSep = ' ';
			}
			else if (fCode.charAt(2) === 'x'){
				d.aSep = '';
			}
			else {
				d.aSep = ',';
			}
			if (fCode.charAt(3) === '2'){ // digital grouping
				d.dGroup = /(\d)((\d)(\d{2}?)+)$/;
			}
			else if (fCode.charAt(3) === '4'){ // digital grouping
				d.dGroup =  /(\d)((\d{4}?)+)$/;
			}
			else {
				d.dGroup =  /(\d)((\d{3}?)+)$/;
			}
			d.aDec = (fCode.charAt(4) == 'c') ? ',' : '.'; // decimal sepatator
			d.mDec = (fCode.charAt(5) <= '9') ? fCode.charAt(5) * 1 : $('#' + lookUp).val() * 1; // decimal places
			d.rMethod = (fCode.charAt(6) !== '') ? fCode.charAt(6) : 'S'; // rounding method
		}
		return d;
	}
	function countLeft(str, charLeft){
		var chr = '';
		var numLeft = 0; //the number of intergers to the left of the decimal point
		for (j = 0; j < charLeft; j++){ //counts the numeric characters to the left of the decimal point that has a numeric value
			chr = str.charAt(j);
			if (chr >= '0' && chr <= '9'){
				numLeft++;
			}
		}
		return numLeft;
	}
	function autoGroup(iv, d){ // places the thousand separtor
		if (d.aSep != ''){
			iv = iv.split(d.aSep).join('');
			var ivSplit = iv.split(d.aDec);
			var s = ivSplit[0];
			while(d.dGroup.test(s)){
				s = s.replace(d.dGroup, '$1'+d.aSep+'$2');
			}
			if (d.mDec !== 0 && ivSplit.length > 1){
				iv = s + d.aDec + ivSplit[1];
			}
			else {
				iv = s;
			}
		}
		return iv;
	}
	function autoRound(iv, mDec, rMethod){ // rounding function via text
		var ivRounded = '';
		var i = 0;
		var nSign = '';
		iv = iv + ''; // convert to string
		if (iv.charAt(0) == '-'){ //Checks if the iv (input Value)is a negative value
			nSign = (iv * 1 === 0) ? '' : '-'; //determines if the value is zero - if zero no negative sign
			iv = iv.replace('-', ''); // removes the negative sign will be added back later if required
		}
		if ((iv * 1) > 0){
			while (iv.substr(0,1) == '0' && iv.length > 1) {
				iv = iv.substr(1,9999);
			}
		}
		var dPos = iv.lastIndexOf('.'); //decimal postion as an integer
		if (dPos === 0){// prefix with a zero if the decimal point is the first character
			iv = '0' + iv;
			dPos = 1;
		}
		if (dPos == -1 || dPos == iv.length - 1){//Has an integer been passed in?
			if (mDec > 0){
				ivRounded = (dPos == -1) ? iv + '.' : iv;
				for(i = 0; i < mDec; i++){ //pads with zero
						ivRounded += '0';
				}
				return nSign + ivRounded;
			}
			else {
				return nSign + iv;
			}
		}
		var cDec = (iv.length - 1) - dPos;//checks decimal places to determine if rounding is required
		if (cDec == mDec){
			return nSign + iv; //If true return value no rounding required
		}
		if (cDec < mDec){ //Do we already have less than the number of decimal places we want?
			ivRounded = iv; //If so, pad out with zeros
			for(i = cDec; i < mDec; i++){
				ivRounded += '0';
			}
			return nSign + ivRounded;
		}
		var rLength = dPos + mDec; //rounded length of the string after rounding
		var tRound = iv.charAt(rLength + 1) * 1; // test round
		var ivArray = [];// new array
		for(i = 0; i <= rLength; i++){ //populate ivArray with each digit in rLength
			ivArray[i] = iv.charAt(i);
		}
		var odd = (iv.charAt(rLength) == '.') ? (iv.charAt(rLength - 1) % 2) : (iv.charAt(rLength) % 2);
		if ((tRound > 4 && rMethod === 'S') || //Round half up symetric
			(tRound > 4 && rMethod === 'A' && nSign === '') || //Round half up asymetric positive values
			(tRound > 5 && rMethod === 'A' && nSign == '-') || //Round half up asymetric negative values
			(tRound > 5 && rMethod === 's') || //Round half down symetric
			(tRound > 5 && rMethod === 'a' && nSign === '') || //Round half down asymetric positive values
			(tRound > 4 && rMethod === 'a' && nSign == '-') || //Round half down asymetric negative values
			(tRound > 5 && rMethod === 'B') || //Round half even "Banker's Rounding"
			(tRound == 5 && rMethod === 'B' && odd == 1) || //Round half even "Banker's Rounding"
			(tRound > 0 && rMethod === 'C' && nSign === '') || //Round to ceiling toward positive infinite
			(tRound > 0 && rMethod === 'F' && nSign == '-') || //Round to floor toward negative inifinte
			(tRound > 0 && rMethod === 'U')){ //round up away from zero
			for(i = (ivArray.length - 1); i >= 0; i--){ //Round up the last digit if required, and continue until no more 9's are found
				if (ivArray[i] == '.'){
					continue;
				}
				ivArray[i]++;
				if (ivArray[i] < 10){ //if i does not equal 10 no more round up required
					break;
				}
			}
		}
		for (i=0; i <= rLength; i++){ //Reconstruct the string, converting any 10's to 0's
			if (ivArray[i] == '.' || ivArray[i] < 10 || i === 0){//routine to reconstruct non '10'
				ivRounded += ivArray[i];
			}
			else { // converts 10's to 0
				ivRounded += '0';
			}
		}
		if (mDec === 0){ //If there are no decimal places, we don't need a decimal point
			ivRounded = ivRounded.replace('.', '');
		}
		return nSign + ivRounded; //return rounded value
	}
	function autoCheck(iv, ii, d){ //test pasted value for field compliance--
		var getPaste = iv.val();
		if (getPaste.length > 25){ //maximum length of pasted value
			$('#' + ii).val('');
			return true;
		}
		//$.extend(d, autoCode(ii, d)); //update var p with the fields settings
		var allowed = d.aNum + d.aSign + d.aDec;
		var eNeg = '';
		if (d.aSign == '-'){ //escape the negative sign
			eNeg = '\\-';
		}
		var reg = new RegExp('[^'+eNeg+d.aNum+d.aDec+']','gi'); // regular expreession constructor to delete any characters not allowed for the input field.
		var testPaste = getPaste.replace(reg,''); //deletes all characters that are not permeinted in this field
		if (testPaste.lastIndexOf('-') > 0 || testPaste.indexOf(d.aDec) != testPaste.lastIndexOf(d.aDec)){
			testPaste = '';
		}
		var rePaste = '';
		var nNeg = 0;
		var nSign = '';
		var i = 0;
		var s = testPaste.split('');
		for (i=0; i<s.length; i++){ // for loop testing pasted value after non allowable characters have been deleted
			if (i === 0 && s[i] == '-'){ // allows negative symbol to be added if it is the first character
				nNeg = 1;
				nSign = '-';
				continue;
			}
			if (s[i] == d.aDec && s.length -1 == i){ //if the last charter is a decimal point it is dropped
				break;
			}
			if (rePaste.length === 0 && s[i] == '0' && (s[i+1] >= 0 || s[i+1] <= 9)){//controls leading zero
				continue;
			}
			else {
				rePaste = rePaste + s[i];
			}
		}
		rePaste = nSign + rePaste;
		if (rePaste.indexOf(d.aDec) == -1 && rePaste.length > (d.mNum + nNeg)){  // check to see if the maximum & minimum values have been exceeded when no decimal point is present
			rePaste = '';
		}
		if (rePaste.indexOf(d.aDec) > (d.mNum + nNeg)){  // check to see if the maximum & minimum values have been exceeded when the decimal point is present
			rePaste = '';
		}
		if (rePaste.indexOf(d.aDec) != -1 && (d.aDec != '.')){
			rePaste = rePaste.replace(d.aDec, '.');
		}
		rePaste = autoRound(rePaste, d.mDec, d.rMethod);
		if (d.aDec != '.'){
			rePaste = rePaste.replace('.', d.aDec);
		}
		if (rePaste !== '' && d.aSep !== ''){
			rePaste = autoGroup(rePaste, d);
		}
		$('#' + ii).val(rePaste);
	}
	$.fn.autoNumeric.Strip = function(ii){ // stripe format and convert decimal seperator to a period
		var iv = $('#' + ii).val();
		var d = $.extend($.fn.autoNumeric.defaults);
		$.extend(d, autoCode(ii, d));
		var reg = new RegExp('[^'+'\\-'+d.aNum+d.aDec+']','gi'); // regular expreession constructor
		iv = iv.replace(reg,''); //deletes all characters that are not permitted in this field
		var nSign = '';
		if (iv.charAt(0) == '-'){ //Checks if the iv (input Value)is a negative value
			nSign = (iv * 1 === 0) ? '' : '-'; //determines if the value is zero - if zero no negative sign
			iv = iv.replace('-', ''); // removes the negative sign will be added back later if required
		}
		iv = iv.replace(d.aDec, '.');
		if (iv * 1 > 0){
			while (iv.substr(0,1) == '0' && iv.length > 1) {
				iv = iv.substr(1,9999);
			}
		}
		iv = (iv.lastIndexOf('.') === 0) ? ('0' + iv) : iv;
		iv = (iv * 1 === 0) ? '0' : iv;
		return nSign + iv;
	};
	$.fn.autoNumeric.Format = function(ii, iv){ //  function that recieves a numeric string and formats to the target input field
		var d = $.extend($.fn.autoNumeric.defaults);
		$.extend(d, autoCode(ii, d));
		iv = autoRound(iv, d.mDec, d.rMethod);
		var nNeg = 0;
		if (iv.indexOf('-') != -1 && d.aSign === ''){ //deletes negative value
			iv = '';
		}
		else if (iv.indexOf('-') != -1 && d.aSign == '-'){
			nNeg = 1;
		}
		if (iv.indexOf('.') == -1 && iv.length > (d.mNum + nNeg)){  // check to see if the maximum & minimum values have been exceeded when no decimal point is present
			iv = '';
		}
		else if (iv.indexOf('.') > (d.mNum + nNeg)){ // check to see if the maximum & minimum values have been exceeded when a decimal point is present
			iv = '';
		}
		if (d.aDec != '.'){ //replaces the decimal point with the new sepatator
			iv = iv.replace('.', d.aDec);
		}
		return autoGroup(iv, d);
	};
})(jQuery);
