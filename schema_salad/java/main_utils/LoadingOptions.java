package ${package}.utils;

import java.util.Map;
import java.util.HashMap;
import java.util.List;

public class LoadingOptions {
    Fetcher fetcher;
    String fileUri;
    Map<String, String> namespaces;
    List<String> schemas;
    Map<String, Map<String, Object>> idx;

    LoadingOptions(final Fetcher fetcher, final String fileUri, final Map<String, String> namespaces, final List<String> schemas, final Map<String, Map<String, Object>> idx) {
        this.fetcher = fetcher;
        this.fileUri = fileUri;
        this.namespaces = namespaces;
        this.schemas = schemas;
        this.idx = idx;
        /*
        self.vocab = _vocab
        self.rvocab = _rvocab

        if namespaces is not None:
            self.vocab = self.vocab.copy()
            self.rvocab = self.rvocab.copy()
            for k, v in iteritems(namespaces):
                self.vocab[k] = v
                self.rvocab[v] = k
        */
    }

}
