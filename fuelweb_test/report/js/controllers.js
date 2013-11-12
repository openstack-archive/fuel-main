'use strict';

/* Controllers */

function TestResultCtrl($scope, $routeParams, $location, TestResult) {

    $scope.statusList = [];
    $scope.environmentList = [];
    $scope.tags = [];
    $scope.statusListForEnvironments = [];

    $scope.testCaseList = TestResult.query(function(){
        var list = $scope.testCaseList;

        list.forEach(function(item){
            if ( $scope.statusList.indexOf(item.status) == -1 ){
                $scope.statusList.push(item.status);
            }
            if ( $scope.environmentList.indexOf(item.environment) == -1 ){
                $scope.environmentList.push(item.environment);
            }
            $scope.tags = _.union($scope.tags, item.tags);
        });

        for ( var e = 0; e < $scope.environmentList.length; e ++ ){
            for ( var i = 0; i < $scope.statusList.length; i ++ ){
                $scope.statusListForEnvironments.push(
                    {
                        environment:$scope.environmentList[e],
                        status:$scope.statusList[i]
                    }
                );
            }
        }

    });

    $scope.testCaseFilter = {};
    $scope.testCaseFilter.status = $location.search().status || "";
    $scope.testCaseFilter.tags = $location.search().tags || "";
    $scope.testCaseFilter.environment = $location.search().environment || "";

    $scope.$watch("testCaseFilter.status", function(newValue){
        $location.search("status", newValue);
    });

    $scope.$watch("testCaseFilter.tags", function(newValue){
        $location.search("tags", newValue);
    });

    $scope.$watch("testCaseFilter.environment", function(newValue){
        $location.search("environment", newValue);
    });

    $scope.setTestCase=function(testCase){
        $scope.testCase = testCase;
    };

    $scope.fixValue=function(value){
        return value == null ? '': value;
    };

    $scope.showDetails = function( status, tags, environment ){
        $location.search("status", status ? status : "" );
        $location.search("tags", tags ? tags : "" );
        $location.search("environment", environment ? environment : "" );
        $location.path("/tests");
    };

    $scope.showLog = function (testCase) {
        $location.path("/tests/{id}".replace("{id}", testCase ));
    }
}

function TestCaseCtrl($scope, $routeParams, $location, TestResult) {
    $scope.testCaseId = $routeParams.testCaseId;

    $scope.testCaseList = TestResult.query(function(){
        $scope.testCaseList.forEach(function(item){
            if ( item.id == $scope.testCaseId  ){
                $scope.testCase = item;
            }
        });
    });

    $scope.back = function(){
        $location.path("/tests/{hash}".replace("{hash}", $location.hash()));
    };

    $scope.getBtnClass = function( status ){
        switch (status){
            case "pass":
                return "btn-success";
            case "fail":
                return "btn-danger";
            case "skip":
                return "btn-info";
            default:
                return "btn-default";
        }
    };

    $scope.getTextClass = function( status ){
        switch (status){
            case "pass":
                return "text-success";
            case "fail":
                return "text-danger";
            case "skip":
                return "text-info";
            default:
                return "";
        }
    };

    $scope.getStatusIcon = function( testStep, visible ){
        if ( testStep.steps.length > 0 ){
            return visible ? "pointer glyphicon glyphicon-collapse-up" : "pointer glyphicon glyphicon-collapse-down";
        }
        return "glyphicon glyphicon-unchecked";
    };





}