/*=========================================================================

  Program:   iota2
  Language:  C++

  Copyright (c) CESBIO. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/
#include <cstddef>

namespace iota2
{
template <typename PixelType>
struct FeatureExtractionFunctor
{
  FeatureExtractionFunctor() = default;
  FeatureExtractionFunctor(size_t cpd) : m_ComponentsPerDate{cpd} {};

  PixelType operator()(const PixelType& p)
  {
    PixelType result{p};

    return result;
  }
  size_t m_ComponentsPerDate;
};
} // end namespace iota2

