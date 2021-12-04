import { Loader, LoadingOptions, ValidationException } from '../internal'

export class AnyLoader implements Loader {
  async load (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string | undefined): Promise<any> {
    if (doc != null) {
      return doc
    }
    throw new ValidationException('Expected non-null')
  }
}
