import { LoadingOptions, Loader, TypeGuards } from '../internal'
import * as yaml from 'js-yaml'

export async function documentLoad (loader: Loader, doc: unknown, baseuri: string, loadingOptions: LoadingOptions): Promise<any> {
  if (typeof doc === 'string') {
    await documentLoadByUrl(loader, loadingOptions.fetcher.urljoin(baseuri, doc), loadingOptions)
  }

  if (Array.isArray(doc)) {
    return await loader.load(doc, baseuri, loadingOptions)
  }

  if (TypeGuards.isDictionary(doc)) {
    if (doc != null) {
      if ('$namespaces' in doc || '$schemas' in doc) {
        loadingOptions = new LoadingOptions({ copyFrom: loadingOptions, namespaces: doc.$namespaces ?? undefined, schemas: doc.$schemas ?? undefined })
        delete doc.$schemas
        delete doc.$namespaces
      }

      if ('$base' in doc) {
        baseuri = doc.$base
      }

      if ('$graph' in doc) {
        return await loader.load(doc.$graph, baseuri, loadingOptions)
      } else {
        return await loader.load(doc, baseuri, loadingOptions)
      }
    }
  }

  throw new Error('Reached unexpected path')
}

export async function documentLoadByUrl (loader: Loader, url: string, loadingOptions: LoadingOptions): Promise<void> {
  if (url in loadingOptions.idx) {
    return await documentLoad(loader, loadingOptions.idx[url], url, loadingOptions)
  }
  const text = await loadingOptions.fetcher.fetchText(url)
  const result = yaml.load(text)
  loadingOptions.idx[url] = result
  loadingOptions = new LoadingOptions({ copyFrom: loadingOptions, fileUri: url })
  return await documentLoad(loader, result, url, loadingOptions)
}
