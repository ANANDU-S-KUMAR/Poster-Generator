export interface PosterRequest{
    title: string;
    description: string;
    genre: string;
}

export interface PosterStatus{
    job_id: string
    status: string
    best_img: string
    other_img: string[]
    error: string
    message:string
}

