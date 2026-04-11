import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterOutlet } from '@angular/router';
import { Poster } from "../poster/poster";

@Component({
  selector: 'app-root',
  imports: [CommonModule, ReactiveFormsModule, Poster],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('poster_generator');
}
