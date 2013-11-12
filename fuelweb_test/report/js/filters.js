var testResultModule = angular.module('testresultFilters', []);

testResultModule.filter('unique',function(){
    return function(items,field){
        var ret = [], found={};
        for(var i in items){
            var item = items[i][field];
            if(!found[item]){
                found[item]=true;
                ret.push(items[i]);
            }
        }
        return ret;
    }
});
