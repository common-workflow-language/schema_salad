import { Saveable, Loader, LoadingOptions, TypeGuards, ValidationException } from '../Internal'

export class _RecordLoader implements Loader {
  creatorFunc: (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string) => Promise<Saveable>
  constructor (createrFunc: (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string) => Promise<Saveable>) {
    this.creatorFunc = createrFunc
  }

  async load (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<Saveable> {
    if (!TypeGuards.isDictionary(doc)) {
      throw new ValidationException('Expected a dict')
    }
    return await this.creatorFunc(doc, baseuri, loadingOptions, docRoot)
  }
}
