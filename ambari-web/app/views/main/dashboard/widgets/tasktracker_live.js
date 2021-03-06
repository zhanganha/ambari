/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var App = require('app');

App.TaskTrackerUpView = App.DashboardWidgetView.extend({

  templateName: require('templates/main/dashboard/widgets/simple_text'),
  title: Em.I18n.t('dashboard.widgets.TaskTrackerUp'),
  id: '8',

  isPieChart: false,
  isText: true,
  isProgressBar: false,
  model_type: 'mapreduce',

  hiddenInfo: function () {
    var svc = this.get('model');
    var liveCount = svc.get('aliveTrackers').get('length');
    var totalCount = svc.get('taskTrackers').get('length');
    var result = [];
    result.pushObject(liveCount + " live");
    result.pushObject(totalCount + " total");
    return result;
  }.property('model.aliveTrackers.length', 'model.taskTrackers.length'),

  classNameBindings: ['isRed', 'isOrange', 'isGreen'],
  isRed: function () {
    var thresh1 = this.get('thresh1');
    var thresh2 = this.get('thresh2');
    return this.get('data') <= thresh1? true: false;
  }.property('data','thresh1','thresh2'),
  isOrange: function () {
    var thresh1 = this.get('thresh1');
    var thresh2 = this.get('thresh2');
    return (this.get('data') <= thresh2 && this.get('data') > thresh1 )? true: false;
  }.property('data','thresh1','thresh2'),
  isGreen: function () {
    var thresh1 = this.get('thresh1');
    var thresh2 = this.get('thresh2');
    return this.get('data') > thresh2? true: false;
  }.property('data','thresh1','thresh2'),

  thresh1: 40,
  thresh2: 70,
  maxValue: 100,

  data: function () {
    return ((this.get('model.aliveTrackers.length')/ this.get('model.taskTrackers.length')).toFixed(2)) * 100;
  }.property('model.taskTrackers.length', 'model.aliveTrackers.length'),

  content: function () {
    return this.get('model.aliveTrackers.length') + "/" + this.get('model.taskTrackers.length');
  }.property('model.taskTrackers.length', 'model.aliveTrackers.length'),

  editWidget: function (event) {
    var parent = this;
    var max_tmp =  parseFloat(parent.get('maxValue'));
    var configObj = Ember.Object.create({
      thresh1: parent.get('thresh1') + '',
      thresh2: parent.get('thresh2') + '',
      hintInfo: 'Edit the percentage of thresholds to change the color of current widget. ' +
        ' Assume all task trackers UP is 100, and all DOWN is 0. '+
        ' So enter two numbers between 0 to ' + max_tmp,
      isThresh1Error: false,
      isThresh2Error: false,
      errorMessage1: "",
      errorMessage2: "",
      maxValue: max_tmp,
      observeNewThresholdValue: function () {
        var thresh1 = this.get('thresh1');
        var thresh2 = this.get('thresh2');
        if (thresh1.trim() != "") {
          if (isNaN(thresh1) || thresh1 > max_tmp || thresh1 < 0) {
            this.set('isThresh1Error', true);
            this.set('errorMessage1', 'Invalid! Enter a number between 0 - ' + max_tmp);
          } else if (this.get('isThresh2Error') === false && parseFloat(thresh2)<= parseFloat(thresh1)){
            this.set('isThresh1Error', true);
            this.set('errorMessage1', 'Threshold 1 should be smaller than threshold 2 !');
          } else {
            this.set('isThresh1Error', false);
            this.set('errorMessage1', '');
          }
        } else {
          this.set('isThresh1Error', true);
          this.set('errorMessage1', 'This is required');
        }

        if (thresh2.trim() != "") {
          if (isNaN(thresh2) || thresh2 > max_tmp || thresh2 < 0) {
            this.set('isThresh2Error', true);
            this.set('errorMessage2', 'Invalid! Enter a number between 0 - ' + max_tmp);
          } else {
            this.set('isThresh2Error', false);
            this.set('errorMessage2', '');
          }
        } else {
          this.set('isThresh2Error', true);
          this.set('errorMessage2', 'This is required');
        }

        // update the slider handles and color
        if (this.get('isThresh1Error') === false && this.get('isThresh2Error') === false) {
          $("#slider-range").slider('values', 0 , parseFloat(thresh1));
          $("#slider-range").slider('values', 1 , parseFloat(thresh2));
        }
      }.observes('thresh1', 'thresh2')
    });

    var browserVerion = this.getInternetExplorerVersion();
    App.ModalPopup.show({
      header: 'Customize Widget',
      classNames: [ 'sixty-percent-width-modal-edit-widget'],
      bodyClass: Ember.View.extend({
        templateName: require('templates/main/dashboard/edit_widget_popup'),
        configPropertyObj: configObj
      }),
      primary: Em.I18n.t('common.apply'),
      onPrimary: function() {
        configObj.observeNewThresholdValue();
        if (!configObj.isThresh1Error && !configObj.isThresh2Error) {
          parent.set('thresh1', parseFloat(configObj.get('thresh1')) );
          parent.set('thresh2', parseFloat(configObj.get('thresh2')) );
          if (!App.testMode) {
            //save to persit
            var big_parent = parent.get('parentView');
            big_parent.getUserPref(big_parent.get('persistKey'));
            var oldValue = big_parent.get('currentPrefObject');
            oldValue.threshold[parseInt(parent.id)] = [configObj.get('thresh1'), configObj.get('thresh2')];
            big_parent.postUserPref(big_parent.get('persistKey'),oldValue);
          }
          this.hide();
        }
      },
      secondary : Em.I18n.t('common.cancel'),
      onSecondary: function () {
        this.hide();
      },

      didInsertElement: function () {
        var handlers = [configObj.get('thresh1'), configObj.get('thresh2')];
        var colors = ['#B80000', '#FF8E00', '#95A800']; //color red, orange, green

        if (browserVerion == -1 || browserVerion > 9) {
          configObj.set('isIE9', false);
          configObj.set('isGreenOrangeRed', false);
          $("#slider-range").slider({
            range: true,
            min: 0,
            max: max_tmp,
            values: handlers,
            create: function (event, ui) {
              updateColors(handlers);
            },
            slide: function (event, ui) {
              updateColors(ui.values);
              configObj.set('thresh1', ui.values[0] + '');
              configObj.set('thresh2', ui.values[1] + '');
            },
            change: function (event, ui) {
              updateColors(ui.values);
            }
          });

          function updateColors(handlers) {
            var colorstops = colors[0] + ", "; // start with the first color
            for (var i = 0; i < handlers.length; i++) {
              colorstops += colors[i] + " " + handlers[i] + "%,";
              colorstops += colors[i+1] + " " + handlers[i] + "%,";
            }
            // end with the last color
            colorstops += colors[colors.length - 1];
            var css1 = '-webkit-linear-gradient(left,' + colorstops + ')'; // chrome & safari
            $('#slider-range').css('background-image', css1);
            var css2 = '-ms-linear-gradient(left,' + colorstops + ')'; // IE 10+
            $('#slider-range').css('background-image', css2);
            //$('#slider-range').css('filter', 'progid:DXImageTransform.Microsoft.gradient( startColorStr= ' + colors[0] + ', endColorStr= ' + colors[2] +',  GradientType=1 )' ); // IE 10-
            var css3 = '-moz-linear-gradient(left,' + colorstops + ')'; // Firefox
            $('#slider-range').css('background-image', css3);

            $('#slider-range .ui-widget-header').css({'background-color': '#FF8E00', 'background-image': 'none'}); // change the  original ranger color
          }
        } else {
          configObj.set('isIE9', true);
          configObj.set('isGreenOrangeRed', false);
        }
      }
    });
  }

})
