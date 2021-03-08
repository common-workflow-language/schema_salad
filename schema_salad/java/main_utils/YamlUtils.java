package ${package}.utils;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.regex.Pattern;

import org.snakeyaml.engine.v2.api.Load;
import org.snakeyaml.engine.v2.api.LoadSettings;
import org.snakeyaml.engine.v2.nodes.Tag;
import org.snakeyaml.engine.v2.resolver.ScalarResolver;

// Copied from org.snakeyaml.engine.v2.resolver.ResolverTuple because it was marked non-public
/**
 * Copyright (c) 2018, http://www.snakeyaml.org
 * <p>
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * <p>
 * http://www.apache.org/licenses/LICENSE-2.0
 * <p>
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
final class ResolverTuple {
	private final Tag tag;
	private final Pattern regexp;

	public ResolverTuple(Tag tag, Pattern regexp) {
		Objects.requireNonNull(tag, "Tag must be provided");
		Objects.requireNonNull(regexp, "regexp must be provided");
		this.tag = tag;
		this.regexp = regexp;
	}

	public Tag getTag() {
		return tag;
	}

	public Pattern getRegexp() {
		return regexp;
	}

	@Override
	public String toString() {
		return "Tuple tag=" + tag + " regexp=" + regexp;
	}
}


// Adapted from org.snakeyaml.engine.v2.resolver.JsonScalarResolver
// Not guaranteed to be complete coverage of the YAML 1.2 Core Schema
// 2021-02-03 Supports 'True'/'False'/'TRUE','FALSE' as boolean; 'Null', 'NULL', an '~' as null
/**
 * Copyright (c) 2018, http://www.snakeyaml.org
 * <p>
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * <p>
 * http://www.apache.org/licenses/LICENSE-2.0
 * <p>
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
class CoreScalarResolver implements ScalarResolver {
	public final Pattern BOOL = Pattern.compile("^(?:true|false|True|False|TRUE|FALSE)$");
	public static final Pattern FLOAT = Pattern
			.compile("^(-?(0?\\.[0-9]+|[1-9][0-9]*(\\.[0-9]*)?)(e[-+]?[0-9]+)?)|-?\\.(?:inf)|\\.(?:nan)$"); // NOSONAR
	public static final Pattern INT = Pattern.compile("^(?:-?(?:0|[1-9][0-9]*))$");
	public static final Pattern NULL = Pattern.compile("^(?:null|Null|NULL|~)$");
	public static final Pattern EMPTY = Pattern.compile("^$");

	public static final Pattern ENV_FORMAT = Pattern
			.compile("^\\$\\{\\s*((?<name>\\w+)((?<separator>:?(-|\\?))(?<value>\\w+)?)?)\\s*\\}$");

	protected Map<Character, List<ResolverTuple>> yamlImplicitResolvers = new HashMap<Character, List<ResolverTuple>>();

	public void addImplicitResolver(Tag tag, Pattern regexp, String first) {
		if (first == null) {
			List<ResolverTuple> curr = yamlImplicitResolvers.computeIfAbsent(null, c -> new ArrayList<ResolverTuple>());
			curr.add(new ResolverTuple(tag, regexp));
		} else {
			char[] chrs = first.toCharArray();
			for (int i = 0, j = chrs.length; i < j; i++) {
				Character theC = Character.valueOf(chrs[i]);
				if (theC == 0) {
					// special case: for null
					theC = null;
				}
				List<ResolverTuple> curr = yamlImplicitResolvers.get(theC);
				if (curr == null) {
					curr = new ArrayList<ResolverTuple>();
					yamlImplicitResolvers.put(theC, curr);
				}
				curr.add(new ResolverTuple(tag, regexp));
			}
		}
	}

	protected void addImplicitResolvers() {
		addImplicitResolver(Tag.NULL, EMPTY, null);
		addImplicitResolver(Tag.BOOL, BOOL, "tfTF");
		/*
		 * INT must be before FLOAT because the regular expression for FLOAT matches INT
		 * (see issue 130) http://code.google.com/p/snakeyaml/issues/detail?id=130
		 */
		addImplicitResolver(Tag.INT, INT, "-0123456789");
		addImplicitResolver(Tag.FLOAT, FLOAT, "-0123456789.");
		addImplicitResolver(Tag.NULL, NULL, "nN~\u0000");
		addImplicitResolver(Tag.ENV_TAG, ENV_FORMAT, "$");
	}

	public CoreScalarResolver() {
		addImplicitResolvers();
	}

	@Override
	public Tag resolve(String value, Boolean implicit) {
		if (!implicit) {
			return Tag.STR;
		}
		final List<ResolverTuple> resolvers;
		if (value.length() == 0) {
			resolvers = yamlImplicitResolvers.get('\0');
		} else {
			resolvers = yamlImplicitResolvers.get(value.charAt(0));
		}
		if (resolvers != null) {
			for (ResolverTuple v : resolvers) {
				Tag tag = v.getTag();
				Pattern regexp = v.getRegexp();
				if (regexp.matcher(value).matches()) {
					return tag;
				}
			}
		}
		if (yamlImplicitResolvers.containsKey(null)) {
			for (ResolverTuple v : yamlImplicitResolvers.get(null)) {
				Tag tag = v.getTag();
				Pattern regexp = v.getRegexp();
				if (regexp.matcher(value).matches()) {
					return tag;
				}
			}
		}
		return Tag.STR;
	}
}

public class YamlUtils {

	public static Map<String, Object> mapFromString(final String text) {
		LoadSettings settings = LoadSettings.builder().setScalarResolver(new CoreScalarResolver()).build();
		Load load = new Load(settings);
		final Map<String, Object> result = (Map<String, Object>) load.loadFromString(text);
		return result;
	}

	public static List<Object> listFromString(final String text) {
		LoadSettings settings = LoadSettings.builder().setScalarResolver(new CoreScalarResolver()).build();
		Load load = new Load(settings);
		final List<Object> result = (List<Object>) load.loadFromString(text);
		return result;
	}
}
