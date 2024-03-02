// Copyright 2023 Two Six Technologies
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

import { Button, ButtonProps } from '@blueprintjs/core';
import clsx from 'clsx';
import { useCallback, useEffect, useState } from 'react';

import styles from './ScrollToTop.module.css';

export type ScrollToTopProps = Omit<ButtonProps, 'onClick'> & {
  absolute?: boolean;
  element?: HTMLElement | null;
  top?: number;
};

export const ScrollToTop = ({
  absolute = true,
  className,
  element = document.documentElement,
  top = 20,
  ...props
}: ScrollToTopProps) => {
  const [visible, setVisible] = useState(true);

  const scrollToTop = useCallback(
    () => element && element.scrollTo({ top: 0, behavior: 'smooth' }),
    [element]
  );

  useEffect(() => {
    if (element) {
      // Register a scroll event listener, and mark visible if scrollTop exceeds the top prop
      const onScroll = () => {
        setVisible(element.scrollTop >= top);
      };
      onScroll();
      element.addEventListener('scroll', onScroll);
      return () => element.removeEventListener('scroll', onScroll);
    }
  }, [element, top]);

  if (visible) {
    return (
      <Button
        className={clsx(className, {
          [styles.absolute]: absolute,
        })}
        icon="arrow-up"
        onClick={scrollToTop}
        {...props}
      />
    );
  }

  return null;
};
