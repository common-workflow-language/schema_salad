package ${package}.utils;

import java.util.List;
import java.util.Map;
import org.yaml.snakeyaml.Yaml;

public class YamlUtils {

  public static Map<String, Object> mapFromString(final String text) {
    Yaml yaml = new Yaml();
    final Map<String, Object> result = yaml.load(text);
    return result;
  }

  public static List<Object> listFromString(final String text) {
    Yaml yaml = new Yaml();
    final List<Object> result = yaml.load(text);
    return result;
  }
}
