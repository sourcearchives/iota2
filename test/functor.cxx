/*=========================================================================

  Program:   
  Language:  C++

  Copyright (c) CESBIO. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/
#include "itkMacro.h"
#include "extractSortedIndices.h"
#include "itkVariableLengthVector.h"

int functor(int itkNotUsed(argc), char * itkNotUsed(argv)[])
{
  using ValueType = float;
  using PixelType = itk::VariableLengthVector<ValueType>;

  std::vector<ValueType> inVec{2,5,1,0,50,6,1,80,4,10};
  std::vector<ValueType> maskVec{0,1,1,0,0,0,0,1,0,0};
  std::vector<ValueType> maskVec_err{1,0};

  auto pars = ESI::FeatureExtractionWithMaskFunctor<PixelType>::Parameters{};
  return EXIT_SUCCESS;
}
