import { Saveable, Loader, LoadingOptions, TypeGuards, ValidationException } from '../Internal'

export class _RecordLoader implements Loader {
  creatorFunc: (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string) => Promise<Saveable>
  container?: string

  constructor (createrFunc: (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string) => Promise<Saveable>, container?: string) {
    this.creatorFunc = createrFunc
    this.container = container
  }

  async load (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<Saveable> {
    if (!TypeGuards.isDictionary(doc)) {
      throw new ValidationException('Expected a dict')
    }
    if (this.container !== undefined) {
      loadingOptions = new LoadingOptions({ copyFrom: loadingOptions, container: this.container })
    }
    return await this.creatorFunc(doc, baseuri, loadingOptions, docRoot)
  }
}
