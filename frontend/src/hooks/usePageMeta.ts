import { useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { updateMetaTags, getPageMetaData } from '../utils/metaUtils';

// 페이지별 메타데이터를 설정하는 훅
export const usePageMeta = (page: string) => {
  const { language } = useLanguage();

  useEffect(() => {
    const metaData = getPageMetaData(page, language);
    updateMetaTags(metaData);
  }, [page, language]);
};