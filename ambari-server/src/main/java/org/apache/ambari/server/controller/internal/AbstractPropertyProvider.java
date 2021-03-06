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

package org.apache.ambari.server.controller.internal;

import org.apache.ambari.server.controller.spi.PropertyProvider;
import org.apache.ambari.server.controller.utilities.PropertyHelper;

import java.util.HashMap;
import java.util.Map;

/**
 *  Abstract property provider implementation.
 */
public abstract class AbstractPropertyProvider extends BaseProvider implements PropertyProvider {

  /**
   * The property/metric information for this provider keyed by component name / property id.
   */
  private final Map<String, Map<String, PropertyInfo>> componentMetrics;


  // ----- Constructors ------------------------------------------------------

  /**
   * Construct a provider.
   *
   * @param componentMetrics map of metrics for this provider
   */
  public AbstractPropertyProvider(Map<String, Map<String, PropertyInfo>> componentMetrics) {
    super(PropertyHelper.getPropertyIds(componentMetrics));
    this.componentMetrics = componentMetrics;
  }


  // ----- accessors ---------------------------------------------------------

  /**
   * Get the map of metrics for this provider.
   *
   * @return the map of metric / property info.
   */
  public Map<String, Map<String, PropertyInfo>> getComponentMetrics() {
    return componentMetrics;
  }


  // ----- helper methods ----------------------------------------------------

  /**
   * Get a map of metric / property info based on the given component name and property id.
   * Note that the property id may map to multiple metrics if the property id is a category.
   *
   * @param componentName  the component name
   * @param propertyId     the property id; may be a category
   *
   * @return a map of metrics
   */
  protected Map<String, PropertyInfo> getPropertyInfoMap(String componentName, String propertyId) {
    Map<String, PropertyInfo> propertyInfoMap = new HashMap<String, PropertyInfo>();

    getPropertyInfoMap(componentName, propertyId, propertyInfoMap);

    return propertyInfoMap;
  }

  // TODO : added for FLUME and reg exp property ids... revisit.
  protected boolean getPropertyInfoMap(String componentName, String propertyId, Map<String, PropertyInfo> propertyInfoMap) {
    Map<String, PropertyInfo> componentMetricMap = componentMetrics.get(componentName);

    propertyInfoMap.clear();

    if (componentMetricMap == null) {
      return false;
    }

    PropertyInfo propertyInfo = componentMetricMap.get(propertyId);
    if (propertyInfo != null) {
      propertyInfoMap.put(propertyId, propertyInfo);
      return false;
    }

    String regExpKey = getRegExpKey(propertyId);

    if (regExpKey != null) {
      propertyInfo = componentMetricMap.get(regExpKey);
      if (propertyInfo != null) {
        propertyInfoMap.put(regExpKey, propertyInfo);
        return true;
      }
    }

    // TODO : For now, if the property info map contains any metrics with regular expressions then get back all the metrics.
    boolean requestAllMetrics = false;

    if (!propertyId.endsWith("/")){
      propertyId += "/";
    }

    for (Map.Entry<String, PropertyInfo> entry : componentMetricMap.entrySet()) {
      if (entry.getKey().startsWith(propertyId)) {
        String key = entry.getKey();
        requestAllMetrics = isPatternKey(key);
        propertyInfoMap.put(key, entry.getValue());
      }
    }

    if (regExpKey != null) {
      if (!regExpKey.endsWith("/")){
        regExpKey += "/";
      }

      for (Map.Entry<String, PropertyInfo> entry : componentMetricMap.entrySet()) {
        if (entry.getKey().startsWith(regExpKey)) {
          requestAllMetrics = true;
          propertyInfoMap.put(entry.getKey(), entry.getValue());
        }
      }
    }
    return requestAllMetrics;
  }
}
