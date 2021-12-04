import { LoadingOptions } from './internal'

// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export abstract class Saveable {
  static async fromDoc (doc: any, baseuri: string, loadingOptions: LoadingOptions, docRoot?: string): Promise<Saveable> {
    throw new Error('Not Implemented')
  }
}
