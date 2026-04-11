import { CommonModule, AsyncPipe } from '@angular/common';
import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit } from '@angular/core';
import { PosterService } from '../service/poster-service';
import { FormBuilder, FormsModule, NgModel, Validators } from '@angular/forms';
import { PosterRequest, PosterStatus } from '../models/poster_data';
import { interval, Subject, switchMap, takeUntil } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-poster',
  imports: [CommonModule, FormsModule],
  templateUrl: './poster.html',
  styleUrl: './poster.css',
})
export class Poster implements OnInit, OnDestroy {
  private posterService = inject(PosterService);
  private cdr = inject(ChangeDetectorRef);
  private fb = inject(FormBuilder);
  poster = this.posterService.poster;
  best_img = '';
  poster_images: string[] = [];
  backgroundImage = '';
  stop$ = new Subject<void>();

  genre_options = [
    'drama',
    'comedy',
    'action',
    'romance',
    'horror',
    'sci-fi',
    'thriller',
    'fantasy',
  ];

  posterForm = this.fb.group({
    title: [this.poster().title, [Validators.required]],
    description: [this.poster().description, [Validators.required]],
    genre: [this.poster().genre, [Validators.required]],
  });
  title: string = '';
  description: string = '';
  genre: string = '';
  generating_poster = false;
  job_id: string = '';

  constructor() {
  }

  ngOnInit() {}

  generatePoster() {
    const poster_request: PosterRequest = {
      title: this.title,
      description: this.description,
      genre: this.genre,
    };
    this.generating_poster = true;
    this.posterService.generatePoster(poster_request).subscribe({
      next: (res: PosterStatus) => {
        if (res.job_id) {
          this.job_id = res.job_id;
          this.checkStatus();
        } else {
          this.generating_poster = false;
        }
      },
      error: (err: HttpErrorResponse) => {
        console.log(err);
        this.stopGenerating();
      },
    });
  }

  checkStatus() {
    interval(10000)
      .pipe(
        switchMap(() => this.posterService.get_status(this.job_id)),
        takeUntil(this.stop$),
      )
      .subscribe({
        next: (res: PosterStatus) => {
          if (res?.status == 'completed') {
            this.best_img = this.posterService.get_img_url(res.best_img); //res.best_img;
            this.poster_images.push(this.best_img);
            res.other_img?.forEach((img) =>
              this.poster_images.push(this.posterService.get_img_url(img)),
            );
            console.log(res);
            this.generating_poster = false;
            this.stop$.next();
            this.cdr.detectChanges();
          }
        },
        error: (err: HttpErrorResponse) => {
          console.log(err);
          this.stopGenerating();
        },
      });
  }

  isGenerating() {
    if (this.generating_poster || !this.title || !this.description) {
      return true;
    }
    return false;
  }

  downloadPoster() {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = this.best_img;

    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx?.drawImage(img, 0, 0);

      canvas.toBlob((blob) => {
        if (!blob) return;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.title || 'poster'}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }, 'image/png');
    };
  }

  ngOnDestroy(): void {
    this.stop$.next();
  }

  selectCandidate(img: string) {
    this.best_img = img;
  }

  stopGenerating() {
    this.generating_poster = false;
    this.stop$.next();
    this.cdr.detectChanges();
  }
}
