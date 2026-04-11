import { Injectable, signal } from '@angular/core';
import { PosterRequest, PosterStatus } from '../models/poster_data';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class PosterService {
  constructor(private http: HttpClient) {}
  private base_url = environment.base_url // Replace it with 

  private state = signal<PosterRequest>({
    title: '',
    description: '',
    genre: ''
  });

  readonly poster = this.state.asReadonly();

  public generatePoster(request: PosterRequest): Observable<PosterStatus> {
    debugger
    const api_url = this.base_url + '/generate_poster/';
    return this.http.post<PosterStatus>(api_url, request);
  }

  public get_status(id:string): Observable<PosterStatus> {
    const api_url = this.base_url + '/status/' + id;
    return this.http.get<PosterStatus>(api_url);
  }

  public get_img_url(img_name: string) {
    return this.base_url + img_name;
  }
  



}
