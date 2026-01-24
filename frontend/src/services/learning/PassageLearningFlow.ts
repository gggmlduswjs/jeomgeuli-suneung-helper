/**
 * Template Method Pattern - Passage Learning Flow
 * 지문 학습 플로우 구현
 */
import { LearningFlow } from './LearningFlow';
import { examAPI, type PassageStructure } from '../../lib/api';

export class PassageLearningFlow extends LearningFlow {
  private passage: string = '';
  private structure: PassageStructure | null = null;

  constructor(passage: string) {
    super(1); // 지문은 단일 항목
    this.passage = passage;
  }

  protected async initialize(): Promise<void> {
    // 초기화 로직
  }

  protected async loadContent(): Promise<void> {
    // 지문 분석
    this.structure = await examAPI.analyzePassage(this.passage);
    await this.loadCurrentItem();
  }

  protected async loadCurrentItem(): Promise<void> {
    // 현재 항목 로드 (이미 분석 완료)
  }

  protected async onComplete(): Promise<void> {
    // 학습 완료 로직
    console.log('[PassageLearningFlow] 학습 완료');
  }

  /**
   * 분석 결과 조회
   */
  getStructure(): PassageStructure | null {
    return this.structure;
  }

  /**
   * 지문 조회
   */
  getPassage(): string {
    return this.passage;
  }
}


